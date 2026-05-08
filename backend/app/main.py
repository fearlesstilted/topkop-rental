import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings

logger = logging.getLogger("topkop")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s (%s)", settings.app_name, settings.app_env)

    yield

    logger.info("Shutdown complete")


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(settings.upload_path)), name="uploads")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


def _include_routers() -> None:
    from app.routers import auth, equipment, inspections, kanban, rentals, utils, ws

    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(equipment.router, prefix="/api/equipment", tags=["equipment"])
    app.include_router(rentals.router, prefix="/api/rentals", tags=["rentals"])
    app.include_router(inspections.router, prefix="/api/inspections", tags=["inspections"])
    app.include_router(kanban.router, prefix="/api/kanban", tags=["kanban"])
    app.include_router(utils.router, prefix="/api/utils", tags=["utils"])
    app.include_router(ws.router, prefix="/ws", tags=["ws"])


try:
    _include_routers()
except ImportError as exc:
    logger.warning("Routers not yet available: %s", exc)
