# Backend Dockerfile - Python 3.12, bind to $PORT (Cloud Run)
FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Dependencies first (better layer caching)
COPY pyproject.toml ./
RUN uv sync --no-dev --no-install-project

# Application code (sync again to install project)
COPY . .
RUN uv sync --no-dev

# Don't run as root
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# Cloud Run sets PORT; default for local
ENV PORT=8080
EXPOSE 8080

# Bind to $PORT (Cloud Run injects PORT)
CMD ["sh", "-c", "uv run uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
