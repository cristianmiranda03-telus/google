# Deploy CV Review — one link, one deploy

**One Cloud Run service.** Open **https://goog-demo-cv0-464316124240.europe-west1.run.app** and you get the full app (frontend + API). No second URL, no extra configuration.

---

## 1. One-time setup

### 1.1 Artifact Registry

```bash
gcloud artifacts repositories create cv_review \
  --repository-format=docker \
  --location=europe-west1 \
  --project=telsalprofessors-dev
```

(Skip if it already exists.)

### 1.2 Connect GitHub to Cloud Build

1. [Cloud Build → Triggers](https://console.cloud.google.com/cloud-build/triggers).
2. **Connect repository** → pick your GitHub repo.
3. Finish the connection.

### 1.3 Create the trigger (single deploy)

1. **Create trigger**.
2. **Name**: e.g. `deploy-goog-demo-cv0`.
3. **Event**: Push to a branch.
4. **Source**: Your connected repo. **Branch**: `^main$` (or your default).
5. **Configuration**: **Cloud Build configuration file (repo)**.
6. **Location**: **`cloudrun/cloudbuild-single.yaml`**.
7. **Substitution variables**:

   | Name          | Value                 |
   |---------------|-----------------------|
   | `_PROJECT_ID` | `telsalprofessors-dev` |
   | `_REGION`     | `europe-west1`        |
   | `_REPO_NAME`  | `cv_review`           |

8. Save.

---

## 2. Deploy

- **Option A**: Push to the branch the trigger watches → build and deploy run automatically.
- **Option B**: In Triggers, open the trigger → **Run**.

When the build finishes, open:

**https://goog-demo-cv0-464316124240.europe-west1.run.app**

You get the app UI (upload CVs, dashboard, etc.). API docs: **/docs**, health: **/api/health**.

---

## 3. Fuelix API key (Cloud Run)

Set the API key as an environment variable on the service:

1. **Cloud Run** → service **goog-demo-cv0** → **Edit & deploy new revision**.
2. **Variables & secrets** → **Add variable** → Name: `FUELIX_API_KEY`, Value: your key.
3. Deploy.

Or with gcloud:

```bash
gcloud run services update goog-demo-cv0 \
  --region=europe-west1 \
  --set-env-vars="FUELIX_API_KEY=your-key" \
  --project=telsalprofessors-dev
```

---

## Summary

| Item | Value |
|------|--------|
| **Config file** | `cloudrun/cloudbuild-single.yaml` |
| **Dockerfile** | `Dockerfile.app` (repo root) |
| **Service** | `goog-demo-cv0` |
| **Region** | `europe-west1` |
| **App URL** | https://goog-demo-cv0-464316124240.europe-west1.run.app |

One deploy, one link, no extra configuration.
