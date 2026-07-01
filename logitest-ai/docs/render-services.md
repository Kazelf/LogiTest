# Render Services Setup

This project deploys one Render Free Web Service for the LogiTest API:

- `logitest-api`: FastAPI LogiTest AI backend.

The repository includes a root `render.yaml` Blueprint. Secrets are intentionally not stored in the file.

## Prerequisites

- GitHub repository is pushed.
- Neon PostgreSQL migration is already applied.
- Neon password was rotated after any accidental sharing.
- Rotated Neon connection string is available privately.

## Blueprint Setup

1. Open Render.
2. Create a new Blueprint from the GitHub repository.
3. Select the root `render.yaml`.
4. Confirm the `logitest-api` service.
5. When Render asks for unsynced environment variables, enter the values below.

## logitest-api

Render Blueprint config:

```text
Root Directory: logitest-ai/apps/api
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Plan: Free
```

Environment variables:

```text
DATABASE_URL=<rotated Neon connection string with sslmode=require>
STAGING_API_BASE_URL=https://<shoplite-service>.onrender.com
ELASTICSEARCH_URL=
DEMO_LOG_INDEX=logitest-demo-logs
```

Smoke check after deploy:

```powershell
Invoke-RestMethod https://<api-service>.onrender.com/health
```

Expected response:

```json
{"status":"ok"}
```

## Notes

- Render Free services can sleep, so open service URLs before a demo.
- `DATABASE_URL` must never be committed to git.
- Hosted Render deployment does not include Elasticsearch. Use local Docker Compose for the full Elasticsearch demo path.
- The hosted free path should use the fallback/mock import flow until cloud Elasticsearch is intentionally added.

