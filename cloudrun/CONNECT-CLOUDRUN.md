# Connect repo to Cloud Run — build configuration

Yes, the repo is ready. Use one of the two options below.

---

## Option A: Cloud Build config file (recommended)

Build and deploy are fully defined in the repo; you only point Cloud Run/Cloud Build at the config file.

### 1. Connect the repo

1. Open **Cloud Run** or **Cloud Build** in Google Cloud Console.
2. **Create Service** (or use an existing one) → **Set up with Cloud Build** / **Continuously deploy from repository**.
3. **Connect repository** → choose your Git provider and repo (e.g. GitHub → your `google` repo).
4. After the repo is connected, continue to **Build configuration**.

### 2. Build configuration

| Field | Value |
|-------|--------|
| **Build configuration type** | **Cloud Build configuration file (yaml or json)** |
| **Cloud Build configuration file location** | **`cloudrun/cloudbuild-single.yaml`** |
| **Source location** | *(leave default — Cloud Build uses the repo root as source)* |

No need to set “Dockerfile” or “Directory” separately; the YAML specifies:
- Dockerfile: `Dockerfile.app`
- Source/context: `.` (repo root)

### 3. Substitution variables (if the UI asks for them)

Add these so the YAML can push images and deploy:

| Name | Value |
|------|--------|
| `_PROJECT_ID` | `telsalprofessors-dev` |
| `_REGION` | `europe-west1` |
| `_REPO_NAME` | `cv_review` |

### 4. Service and region

- **Service name**: `goog-demo-cv0` (or whatever you want).
- **Region**: `europe-west1`.

Save. On the next push (or manual run), Cloud Build will build from `Dockerfile.app` and deploy to Cloud Run.

---

## Option B: Dockerfile-only build

If the UI only lets you choose “Dockerfile” (no config file), use these values:

| Field | Value |
|-------|--------|
| **Build configuration type** | **Dockerfile** |
| **Dockerfile path** | **`Dockerfile.app`** |
| **Source location / Build context / Directory** | **`.`** or **Repository root** |

So:
- **Dockerfile**: `Dockerfile.app`
- **Source location**: `.` (repo root)

---

## Summary

| Question | Answer |
|----------|--------|
| Is the repo ready? | Yes. |
| Build config (recommended) | Use **Cloud Build configuration file** → **`cloudrun/cloudbuild-single.yaml`**. |
| Source location | Repo root (default when using the config file; or set **`.`** if asked). |
| If using Dockerfile only | **Dockerfile path**: `Dockerfile.app` — **Source location**: `.` |

After connecting and saving, the next build will use `Dockerfile.app` and the repo root as source.
