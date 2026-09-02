# syntax=docker/dockerfile:1.7
FROM ghcr.io/astral-sh/uv:0.8.13 AS uv

FROM python:3.13.7-slim AS builder
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
COPY alembic.ini ./
COPY migrations ./migrations
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.13.7-slim AS runtime
RUN groupadd --system woonlens \
    && useradd --system --gid woonlens --home-dir /app woonlens

WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    WOONLENS_ENVIRONMENT=production \
    WOONLENS_LOG_LEVEL=INFO

COPY --from=builder --chown=woonlens:woonlens /app/.venv /app/.venv
USER woonlens
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=2)"]

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn woonlens.entrypoints.api:create_app --factory --host 0.0.0.0 --port 8000 --no-access-log"]

FROM builder AS development
COPY tests ./tests
# Keep the project editable in development so the read-only source bind mount
# is the code Uvicorn imports and reloads.
RUN uv sync --frozen --all-groups
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    WOONLENS_ENVIRONMENT=development \
    WOONLENS_LOG_LEVEL=DEBUG
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn woonlens.entrypoints.api:create_app --factory --host 0.0.0.0 --port 8000 --reload --no-access-log"]
