from fastapi import FastAPI
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from app.api.candidate_applications import CandidateRateLimiter
from app.api.candidate_applications import router as candidate_applications_router
from app.api.router import api_router
from app.core.config import Settings, get_settings


def _candidate_validation_handler(candidate_path: str):
    async def handler(request: Request, exc: RequestValidationError):
        if request.url.path == candidate_path:
            return JSONResponse(
                status_code=422,
                content={"detail": "Invalid candidate application"},
            )
        return await request_validation_exception_handler(request, exc)

    return handler


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    app = FastAPI(
        title=app_settings.project_name,
        debug=app_settings.debug,
        docs_url="/docs" if app_settings.is_development else None,
        redoc_url="/redoc" if app_settings.is_development else None,
        openapi_url="/openapi.json" if app_settings.is_development else None,
    )
    app.state.candidate_rate_limiter = CandidateRateLimiter(
        app_settings.candidate_rate_limit_requests,
        app_settings.candidate_rate_limit_window_seconds,
    )
    if settings is not None:
        app.dependency_overrides[get_settings] = lambda: app_settings

    candidate_path = f"{app_settings.api_v1_prefix}/candidate-applications"
    app.add_exception_handler(RequestValidationError, _candidate_validation_handler(candidate_path))

    app.include_router(api_router, prefix=app_settings.api_v1_prefix)
    if app_settings.candidate_intake_enabled:
        app.include_router(candidate_applications_router, prefix=app_settings.api_v1_prefix)
    return app


app = create_app()
