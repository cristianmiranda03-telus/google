# Single image: frontend (static) + backend. One Cloud Run URL for the full app.
# Build from repo root: docker build -f Dockerfile.app .

# Stage 1: build Next.js static export (same-origin API)
FROM node:20-alpine AS frontend
WORKDIR /app
ENV NEXT_PUBLIC_API_URL=
COPY cv_review/frontend/package.json cv_review/frontend/package-lock.json* ./
RUN npm ci 2>/dev/null || npm install
COPY cv_review/frontend/ .
RUN npm run build

# Stage 2: backend + copy frontend into static
FROM python:3.12-slim
WORKDIR /app

COPY cv_review/backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY cv_review/backend/ .
COPY --from=frontend /app/out ./static

RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
