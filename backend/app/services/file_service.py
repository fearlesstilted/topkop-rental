"""Сохранение фото и подписей на диск. Возвращает относительные пути для БД."""
from __future__ import annotations

import base64
import re
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile

from app.config import get_settings

ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
settings = get_settings()


def _subdir(kind: str) -> Path:
    today = datetime.now().strftime("%Y/%m")
    d = settings.upload_path / kind / today
    d.mkdir(parents=True, exist_ok=True)
    return d


def _ext_from_filename(name: str | None) -> str:
    if not name:
        return ".jpg"
    ext = Path(name).suffix.lower()
    return ext if ext in ALLOWED_IMAGE_EXT else ".jpg"


async def save_upload(upload: UploadFile, kind: str = "photos") -> str:
    data = await upload.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise ValueError(f"File too large: {len(data)} bytes (max {max_bytes})")
    ext = _ext_from_filename(upload.filename)
    name = f"{uuid.uuid4().hex}{ext}"
    abs_path = _subdir(kind) / name
    abs_path.write_bytes(data)
    return str(abs_path.relative_to(settings.upload_path)).replace("\\", "/")


_DATA_URL_RE = re.compile(r"^data:image/(png|jpeg|webp);base64,(.+)$", re.IGNORECASE | re.DOTALL)


def save_data_url(data_url: str, kind: str = "signatures") -> str:
    m = _DATA_URL_RE.match(data_url.strip())
    if not m:
        raise ValueError("Invalid data URL")
    ext = {"png": ".png", "jpeg": ".jpg", "webp": ".webp"}[m.group(1).lower()]
    blob = base64.b64decode(m.group(2))
    name = f"{uuid.uuid4().hex}{ext}"
    abs_path = _subdir(kind) / name
    abs_path.write_bytes(blob)
    return str(abs_path.relative_to(settings.upload_path)).replace("\\", "/")


def absolute_path(relative: str) -> str:
    return str((settings.upload_path / relative).resolve())
