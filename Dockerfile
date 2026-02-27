# Root Dockerfile for Cloud Run (when build context is repo root).
# Builds the backend. Use Dockerfile path "Dockerfile" and context "." in the trigger.
# Alternative: use Dockerfile path "backend/Dockerfile" and context "backend".
FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY backend/pyproject.toml ./
RUN uv sync --no-dev --no-install-project

COPY backend/ .
RUN uv sync --no-dev

RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "uv run uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
