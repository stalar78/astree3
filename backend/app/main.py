from fastapi import FastAPI
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from app.api.admin_auth import AdminLoginRateLimiter
from app.api.candidate_applications import CandidateRateLimiter
from app.api.candidate_applications import router as candidate_applications_router
from app.api.router import api_router
from app.core.config import Settings, get_settings


def _scoped_validation_handler(path_details: tuple[tuple[str, str], ...]):
    async def handler(request: Request, exc: RequestValidationError):
        for path, detail in path_details:
            if request.url.path == path or request.url.path.startswith(f"{path}/"):
                return JSONResponse(
                    status_code=422,
                    content={"detail": detail},
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
    app.state.admin_login_rate_limiter = AdminLoginRateLimiter(
        app_settings.admin_login_rate_limit_requests,
        app_settings.admin_login_rate_limit_window_seconds,
    )
    if settings is not None:
        app.dependency_overrides[get_settings] = lambda: app_settings

    candidate_path = f"{app_settings.api_v1_prefix}/candidate-applications"
    admin_auth_path = f"{app_settings.api_v1_prefix}/admin/auth"
    app.add_exception_handler(
        RequestValidationError,
        _scoped_validation_handler(
            (
                (candidate_path, "Invalid candidate application"),
                (admin_auth_path, "Invalid admin authentication request"),
            ),
        ),
    )

    app.include_router(api_router, prefix=app_settings.api_v1_prefix)
    if app_settings.candidate_intake_enabled:
        app.include_router(candidate_applications_router, prefix=app_settings.api_v1_prefix)
    return app


app = create_app()
