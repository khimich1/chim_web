"""FastAPI application entry point.

Patterns:
- Lifespan: https://fastapi.tiangolo.com/advanced/events/
- CORS: https://fastapi.tiangolo.com/tutorial/cors/
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.api.routers import capture as capture_router
from app.api.routers import custom_themes as custom_themes_router
from app.api.routers import auth as auth_router
from app.api.routers import homework as homework_router
from app.api.routers import student_homework as student_homework_router
from app.api.routers import leaderboard as leaderboard_router
from app.api.routers import notifications as notifications_router
from app.api.routers import students as students_router
from app.api.routers import teacher_stats as teacher_stats_router
from app.api.routers import teacher_themes as teacher_themes_router
from app.api.routers import test_sessions as test_sessions_router
from app.api.routers import tests as tests_router
from app.api.routers import textbook as textbook_router
from app.api.routers import tutor as tutor_router
from app.api.routers import uploads as uploads_router
from app.core.config import Settings, get_settings
from app.core.logging import setup_logging
from app.core.rate_limit import limiter
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
    application.state.limiter = limiter

    @application.exception_handler(RateLimitExceeded)
    async def rate_limit_exceeded_handler(
        _request: Request,
        exc: RateLimitExceeded,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"error": f"Rate limit exceeded: {exc.detail}"},
        )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(auth_router.router)
    application.include_router(students_router.router)
    application.include_router(teacher_stats_router.router)
    application.include_router(leaderboard_router.router)
    application.include_router(homework_router.router)
    application.include_router(student_homework_router.router)
    application.include_router(notifications_router.router)
    application.include_router(textbook_router.router)
    application.include_router(tests_router.router)
    application.include_router(test_sessions_router.router)
    application.include_router(capture_router.router)
    application.include_router(custom_themes_router.router)
    application.include_router(tutor_router.router)
    application.include_router(uploads_router.router)
    application.include_router(teacher_themes_router.router)

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
