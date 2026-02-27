# Deploy full app: backend + frontend (so the frontend link works)

The link **https://goog-demo-cv0-frontend-464316124240.europe-west1.run.app** only works after the **frontend** service is deployed. Right now only the backend (`goog-demo-cv0`) exists. Use one of the two options below.

---

## Option 1: Deploy from your machine (recommended if you haven’t used Cloud Build for this repo)

Run these in **Git Bash** or **PowerShell** from the **repo root** (where `cv_review` and `cloudrun` folders are).

### 1. Set variables

```bash
PROJECT_ID=telsalprofessors-dev
REGION=europe-west1
REPO=cv_review
```

### 2. Create Artifact Registry repo (once)

```bash
gcloud artifacts repositories create $REPO --repository-format=docker --location=$REGION --project=$PROJECT_ID
```

If you get "already exists", skip this step.

### 3. Configure Docker for Artifact Registry

```bash
gcloud auth configure-docker $REGION-docker.pkg.dev --project=$PROJECT_ID
```

### 4. Build and push backend

```bash
docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/backend:latest -f cv_review/backend/Dockerfile cv_review/backend
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/backend:latest
```

### 5. Deploy backend (or update it)

```bash
gcloud run deploy goog-demo-cv0 \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/backend:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --project $PROJECT_ID
```

### 6. Build frontend with your backend URL

Use your real backend URL so the UI calls the right API:

```bash
docker build \
  --build-arg NEXT_PUBLIC_API_URL=https://goog-demo-cv0-464316124240.europe-west1.run.app \
  -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/frontend:latest \
  -f cv_review/frontend/Dockerfile \
  cv_review/frontend
```

### 7. Push and deploy frontend

```bash
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/frontend:latest

gcloud run deploy goog-demo-cv0-frontend \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/frontend:latest \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --project $PROJECT_ID
```

### 8. Open the app

At the end, `gcloud` will print the frontend URL. Or open:

**https://goog-demo-cv0-frontend-464316124240.europe-west1.run.app**

(If your project number is different, check **Cloud Run** in the console for the exact URL.)

---

## Option 2: Deploy via Cloud Build (GitHub trigger)

Use this if you want every push to build and deploy both services.

### 1. Create Artifact Registry repo (once)

```bash
gcloud artifacts repositories create cv_review \
  --repository-format=docker \
  --location=europe-west1 \
  --project=telsalprofessors-dev
```

### 2. Create a Cloud Build trigger

1. Open [Cloud Build → Triggers](https://console.cloud.google.com/cloud-build/triggers).
2. **Create trigger**.
3. **Name**: e.g. `deploy-cv-review-full-app`.
4. **Event**: Push to a branch.
5. **Source**: your connected repo (e.g. `jimenezcr-alt/google` or `cristianmiranda03-telus/google`).
6. **Branch**: `^main$` (or your default branch).
7. **Configuration**:
   - Type: **Cloud Build configuration file (repo)**.
   - Location: **`cloudrun/cloudbuild-app.yaml`**.
8. **Substitution variables** (click **Add variable** for each):

   | Name          | Value                 |
   |---------------|-----------------------|
   | `_PROJECT_ID` | `telsalprofessors-dev`|
   | `_REGION`     | `europe-west1`        |
   | `_REPO_NAME`  | `cv_review`           |

9. Save.

### 3. Run the trigger

- **Run** the trigger from the Triggers page, or  
- **Push a commit** to the branch the trigger watches.

When the build finishes, both services will be deployed and the frontend URL will work.

---

## Summary

- **Backend**: `goog-demo-cv0` → already exists.
- **Frontend**: `goog-demo-cv0-frontend` → you need to deploy it once (Option 1 or 2).
- **App link**: **https://goog-demo-cv0-frontend-464316124240.europe-west1.run.app** (after frontend is deployed).

Use **Option 1** if you want to deploy right now from your machine; use **Option 2** for automatic deploys on every push.
