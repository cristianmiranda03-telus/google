# Cloud Run build configuration

Your build failed because the **Dockerfile path** was set to `backend` (a directory). It must be a path to a **file**.

## Fix in Google Cloud Console

1. Open **Cloud Build** → **Triggers** (or **Cloud Run** → your service → **Set up continuous deployment**).
2. Edit the trigger that builds from `jimenezcr-alt/google`.
3. **Build configuration**:
   - **Dockerfile path**: set to **`backend/Dockerfile`** (or **`Dockerfile`** if you use the root Dockerfile).
   - **Build context / Directory**: set to **`backend`** if using `backend/Dockerfile`, or **`.`** (root) if using root **`Dockerfile`**.

So use **one** of these:

| Dockerfile path       | Build context / Directory |
|----------------------|----------------------------|
| `backend/Dockerfile` | `backend`                  |
| `Dockerfile`         | `.` (root)                 |

4. Save and run the trigger again.

## Root Dockerfile

A **`Dockerfile`** at the repo root is provided. If your trigger uses the repo root as context, set Dockerfile path to **`Dockerfile`** and directory to **`.`** so the build uses this file and succeeds.
