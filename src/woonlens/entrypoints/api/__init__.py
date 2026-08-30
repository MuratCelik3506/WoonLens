from fastapi import FastAPI

from woonlens.bootstrap.settings import Settings, get_settings
from woonlens.entrypoints.api.health import router as health_router


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the HTTP application with explicit configuration."""
    resolved_settings = settings or get_settings()
    app = FastAPI(
        title="WoonLens API",
        version="0.1.0",
        docs_url="/docs" if resolved_settings.environment != "production" else None,
        redoc_url=None,
    )
    app.state.settings = resolved_settings
    app.include_router(health_router, prefix="/api/v1")
    return app


__all__ = ["create_app"]
