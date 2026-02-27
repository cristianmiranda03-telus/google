# Full app deploy (legacy — two services)

**Use the single deploy instead:** see [DEPLOY.md](./DEPLOY.md). One link, one service: **https://goog-demo-cv0-464316124240.europe-west1.run.app**

The instructions below are only if you need separate backend and frontend services.

---

## Option 1: Deploy from your machine

Set variables, then build and deploy frontend after backend is already deployed.

```bash
PROJECT_ID=telsalprofessors-dev
REGION=europe-west1
REPO=cv_review

gcloud artifacts repositories create $REPO --repository-format=docker --location=$REGION --project=$PROJECT_ID  # once
gcloud auth configure-docker $REGION-docker.pkg.dev --project=$PROJECT_ID

# Backend
docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/backend:latest -f cv_review/backend/Dockerfile cv_review/backend
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/backend:latest
gcloud run deploy goog-demo-cv0 --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/backend:latest --region $REGION --platform managed --allow-unauthenticated --project $PROJECT_ID

# Frontend (use your backend URL)
docker build --build-arg NEXT_PUBLIC_API_URL=https://goog-demo-cv0-464316124240.europe-west1.run.app -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/frontend:latest -f cv_review/frontend/Dockerfile cv_review/frontend
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/frontend:latest
gcloud run deploy goog-demo-cv0-frontend --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/frontend:latest --region $REGION --platform managed --allow-unauthenticated --project $PROJECT_ID
```

---

## Option 2: Cloud Build (two services)

Use trigger with **`cloudrun/cloudbuild-app.yaml`** and substitutions `_PROJECT_ID`, `_REGION`, `_REPO_NAME`. This creates both **goog-demo-cv0** and **goog-demo-cv0-frontend**.
