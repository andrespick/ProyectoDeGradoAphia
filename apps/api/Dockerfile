# syntax=docker/dockerfile:1
# API de APHIA con Uvicorn (producción en el VPS). Workers sigue usando pywrangler.

FROM ghcr.io/astral-sh/uv:0.13.6 AS uv

FROM python:3.13-slim AS build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock ./
# Sin el grupo dev (pywrangler, pytest); con el grupo server (uvicorn).
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.13-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"
RUN groupadd --system --gid 10001 aphia \
    && useradd --system --uid 10001 --gid aphia --no-create-home --shell /usr/sbin/nologin aphia
COPY --from=build /opt/venv /opt/venv
WORKDIR /app
COPY src ./src
USER aphia
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2).status == 200 else 1)"]
CMD ["uvicorn", "main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000", "--no-server-header", "--no-access-log"]
