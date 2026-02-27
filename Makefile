# Developer workflow - prefer running via Makefile (e.g. make dev)
.PHONY: dev install backend frontend build deploy-backend deploy-frontend

dev:
	@echo "Run backend: make backend | frontend: make frontend"
	$(MAKE) backend

install:
	cd backend && uv sync
	cd frontend && npm install

backend:
	cd backend && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8080

frontend:
	cd frontend && npm run dev

build:
	$(MAKE) -C backend build 2>/dev/null || true
	cd frontend && npm run build

deploy-backend:
	gcloud run services replace cloudrun/backend-service.yaml --region=europe-west1

deploy-frontend:
	gcloud run services replace cloudrun/frontend-service.yaml --region=europe-west1
