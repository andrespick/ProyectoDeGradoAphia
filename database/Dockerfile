# syntax=docker/dockerfile:1
# Imagen de operaciones para ejecutar migraciones en el VPS dentro de la red privada de Docker.
# Contexto de construcción: raíz del repositorio (ver infra/production/compose.yaml, servicio migrator).

FROM ghcr.io/astral-sh/uv:0.13.6 AS uv

FROM python:3.13-slim
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
# Reutiliza el lockfile de la API: mismas versiones de PyMySQL que en desarrollo y CI.
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN uv sync --frozen --no-default-groups --no-install-project
COPY database /database
RUN useradd --system --uid 10002 --no-create-home --shell /usr/sbin/nologin migrator
USER migrator
ENTRYPOINT ["/opt/venv/bin/python", "/database/scripts/migrate.py"]
