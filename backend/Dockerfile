# Multi-stage build (ADR-006): builder installs deps; slim runtime, non-root.

# ---- Stage 1: builder ----
FROM python:3.12-slim AS builder

RUN pip install --no-cache-dir uv==0.11.16

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app
COPY pyproject.toml uv.lock* README.md ./
# Install runtime deps only (no dev group) into /opt/venv.
RUN uv sync --no-dev --no-install-project

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./alembic.ini
RUN uv sync --no-dev --no-editable

# ---- Stage 2: runtime ----
FROM python:3.12-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN adduser --disabled-password --gecos "" appuser \
    && mkdir -p /data && chown -R appuser:appuser /data

WORKDIR /app
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser migrations ./migrations
COPY --chown=appuser:appuser alembic.ini ./alembic.ini
COPY --chown=appuser:appuser docker-entrypoint.sh ./docker-entrypoint.sh
RUN chmod +x ./docker-entrypoint.sh

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/api/v1/health').status==200 else 1)"

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:get_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
