FROM python:3.13-slim-bookworm AS builder

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN uv export --frozen --no-dev --no-emit-project --output-file /tmp/requirements.txt

RUN --mount=type=cache,target=/root/.cache/pip \
    python -m venv .venv \
 && .venv/bin/pip install --no-cache-dir --compile -r /tmp/requirements.txt

FROM python:3.13-slim-bookworm AS runtime

RUN groupadd --gid 1001 app \
 && useradd --uid 1001 --gid app --shell /sbin/nologin --no-create-home app

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv

COPY --chown=app:app domain/         domain/
COPY --chown=app:app application/    application/
COPY --chown=app:app adapters/       adapters/
COPY --chown=app:app infrastructure/ infrastructure/
COPY --chown=app:app main.py main_api.py main_mcp_http.py main_mcp_sse.py main_mcp_stdio.py main_cli.py __init__.py ./

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MODE=api

USER app

EXPOSE 9026 8026 8024

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9026/health')" || exit 1

CMD ["python", "main.py"]
