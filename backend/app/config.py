from functools import lru_cache
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://topkop:topkop@localhost:5432/excavator"
    database_sync_url: str = "postgresql+psycopg2://topkop:topkop@localhost:5432/excavator"

    app_name: str = "TopKop Rental"
    app_env: str = "development"
    secret_key: str = "change-me"

    pin_default_biuro: str | None = None
    pin_default_manager: str | None = None

    cors_origins: str = "http://localhost:5173,https://localhost:5173"

    upload_dir: str = "./uploads"
    max_upload_mb: int = 15

    # Legacy fields are still consumed by the older inspection PDF template.
    company_name: str = "TOP KOP Gołdap"
    company_address: str = "ul. Graniczna 3, 19-500 Gołdap"
    company_nip: str = "847-16-16-578"
    company_phone: str = "+48 87 520 10 03"
    company_email: str = "biuro.topkop@gmail.com"

    # Default billing entity for most TopKop rental agreements.
    company_jdg_name: str = "TOP KOP Krzysztof Świtaj"
    company_jdg_short: str = "TOP KOP Krzysztof Świtaj"
    company_jdg_address: str = "ul. Graniczna 3, 19-500 Gołdap, Niedrzwica"
    company_jdg_nip: str = "847-16-16-578"
    company_jdg_regon: str = ""
    company_jdg_phone: str = "503 839 393"
    company_jdg_email: str = "biuro.topkop@gmail.com"

    # Corporate billing entity; registry fields are intentionally blank until confirmed.
    company_spzoo_name: str = "TK Sp. z o.o."
    company_spzoo_short: str = "TK Sp. z o.o."
    company_spzoo_address: str = "ul. Graniczna 3, 19-500 Gołdap"
    company_spzoo_nip: str = ""
    company_spzoo_krs: str = ""
    company_spzoo_regon: str = ""
    company_spzoo_phone: str = "503 839 393"
    company_spzoo_email: str = "biuro.topkop@gmail.com"

    @model_validator(mode="after")
    def reject_development_secret_in_production(self) -> "Settings":
        development_secrets = {"change-me", "dev-secret-change-me"}
        if self.app_env.lower() == "production" and self.secret_key in development_secrets:
            raise ValueError("SECRET_KEY must be set to a strong value in production")
        return self

    @field_validator("database_url")
    @classmethod
    def normalize_async_database_url(cls, value: str) -> str:
        parts = urlsplit(value)
        scheme = parts.scheme
        if scheme in {"postgres", "postgresql"}:
            scheme = "postgresql+asyncpg"

        if scheme != "postgresql+asyncpg":
            return value

        query = [
            ("ssl" if key == "sslmode" else key, query_value)
            for key, query_value in parse_qsl(parts.query, keep_blank_values=True)
            if key != "channel_binding"
        ]
        return urlunsplit((scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def upload_path(self) -> Path:
        p = Path(self.upload_dir).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
