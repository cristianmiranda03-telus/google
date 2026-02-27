# Deploy config: Dockerfile and source location

## Reference

| What | Value |
|------|--------|
| **Dockerfile** | `Dockerfile.app` (repo root) |
| **Source location (build context)** | `.` (repo root — directory that contains `cv_review/`, `Dockerfile.app`, etc.) |

The Dockerfile expects to be run **from the repo root**, so paths inside it (e.g. `cv_review/frontend/`) are relative to that root.

---

## 1. Using `make deploy` (local)

**Dockerfile** and **source** are set in the Makefile:

```makefile
docker build -t $(IMAGE) -f Dockerfile.app .
#                            ^^^^^^^^^^^^^^     ^
#                            Dockerfile path     Build context (source location)
```

**To use a different Dockerfile:**

Edit the Makefile, line 36:

```makefile
# Example: use Dockerfile.prod instead
docker build -t $(IMAGE) -f Dockerfile.prod .
```

Or override from the command line (if you add a variable):

```bash
make deploy DOCKERFILE=Dockerfile.prod
```

To support that, add at the top of the Makefile:

```makefile
DOCKERFILE ?= Dockerfile.app
```

and change the build line to:

```makefile
docker build -t $(IMAGE) -f $(DOCKERFILE) .
```

**Source location** is always the current directory (`.`), i.e. wherever you run `make deploy` from (should be repo root).

---

## 2. Using Cloud Build (`cloudrun/cloudbuild-single.yaml`)

**Dockerfile** and **source** are in the build step:

```yaml
steps:
  - id: build
    name: gcr.io/cloud-builders/docker
    args:
      - build
      - -t
      - ${_REGION}-docker.pkg.dev/...
      - -f
      - Dockerfile.app    # <-- Dockerfile path
      - .                 # <-- Source location (build context)
    dir: .                 # <-- Working directory (repo root when source is the repo)
```

**To use a different Dockerfile:**

Change the `-f` value, e.g.:

```yaml
      - -f
      - Dockerfile.prod
      - .
```

**Source location** is the last argument to `docker build` — here `.` (repo root). Cloud Build runs with the repo as the workspace, so `.` is the repo root.

---

## 3. Cloud Run “Deploy from repository” (Console)

If you use the Cloud Run UI **Deploy from repository** instead of a config file:

1. **Cloud Run** → **Create service** (or **Edit** existing) → **Deploy from repository**.
2. **Dockerfile path**: e.g. `Dockerfile.app` (path relative to repo root).
3. **Build context / Source / Directory**: `.` or leave default so the **repository root** is used.

So:

- **Dockerfile path**: `Dockerfile.app` (or `Dockerfile.prod`, etc.).
- **Source location**: repository root (`.`).

---

## Summary

| Method | Dockerfile | Source location |
|--------|------------|------------------|
| `make deploy` | `Dockerfile.app` (Makefile line 36) | `.` (repo root) |
| `cloudbuild-single.yaml` | `Dockerfile.app` (build step `-f`) | `.` (build step last arg) |
| Console “Deploy from repository” | Set in UI, e.g. `Dockerfile.app` | Repo root (`.` or default) |

To switch to a new Dockerfile, change the **Dockerfile** path in one of the three places above; keep **source location** as repo root (`.`).
