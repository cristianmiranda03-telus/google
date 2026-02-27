"""CV review backend - FastAPI app bound to $PORT (Cloud Run)."""

from fastapi import FastAPI

app = FastAPI(
    title="CV Review API",
    description="API for CV review; OpenAPI at /docs",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness/readiness check for Cloud Run."""
    return {"status": "ok"}
