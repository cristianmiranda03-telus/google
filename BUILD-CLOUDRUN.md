# Cloud Run build — one shot

Use **Cloud Build with the config file** so you don’t set Dockerfile path or context by hand.

1. **Cloud Build** → **Triggers** → Create (or edit) trigger.
2. **Configuration**: **Cloud Build configuration file (repo)**.
3. **Location**: **`cloudrun/cloudbuild-single.yaml`**.
4. **Substitutions**: `_PROJECT_ID`, `_REGION`, `_REPO_NAME` (see [cloudrun/DEPLOY.md](cloudrun/DEPLOY.md)).

That’s it. One deploy, one link: **https://goog-demo-cv0-464316124240.europe-west1.run.app**

---

If you were using “Deploy from repository” with a **Dockerfile path** field instead of a config file:

- **Dockerfile path**: `Dockerfile.app`
- **Build context / Directory**: `.` (repo root)

But using **`cloudrun/cloudbuild-single.yaml`** is preferred (one config, no extra setup).
