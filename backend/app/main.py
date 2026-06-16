"""FastAPI application entry point.

Patterns:
- Lifespan: https://fastapi.tiangolo.com/advanced/events/
- CORS: https://fastapi.tiangolo.com/tutorial/cors/
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import auth as auth_router
from app.core.config import Settings, get_settings
from app.core.logging import setup_logging
from app.db.session import dispose_engine, init_engine


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        setup_logging(app_settings.log_level)
        init_engine(app_settings.database_url)
        yield
        await dispose_engine()

    application = FastAPI(
        title="Chemistry API",
        description="chim_web backend — chemistry tutor platform",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.state.settings = app_settings

    application.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(auth_router.router)

    @application.get("/health")
    def health(request: Request) -> dict[str, object]:
        """Liveness check; reports configured content DB file presence."""
        paths = request.app.state.settings.content_db_paths()
        return {
            "status": "ok",
            "content_databases": {
                name: {"path": str(path), "exists": path.is_file()}
                for name, path in paths.items()
            },
        }

    return application


app = create_app()
