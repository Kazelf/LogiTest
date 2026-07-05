# LogiTest + ShopLite

Root-level Docker setup for running the LogiTest AI dashboard/API and the ShopLite demo system together.

## Run the Combined Stack

From this repository root:

```powershell
docker compose up --build
```

This builds one combined app image/container for:

- LogiTest AI dashboard: `http://localhost:3000`
- LogiTest AI API: `http://localhost:8000/health`
- ShopLite frontend: `http://localhost:5173`
- ShopLite API: `http://localhost:4000/health`

The app container uses the root `Dockerfile` and `docker/entrypoint.sh` to start the four app processes together. PostgreSQL and Elasticsearch still run as dependency services because the demo stack depends on those engines.

## Data Services

The root compose file starts one PostgreSQL service with two databases:

- `logitest_ai` for LogiTest AI on host port `5432`
- `shoplite` for ShopLite on host port `5433`

Elasticsearch runs on `http://localhost:9200`.

If you previously created root compose volumes and need a clean database reset:

```powershell
docker compose down -v
docker compose up --build
```

## Manual Debugging

For service-by-service debugging, run the apps manually from their package folders and keep the root compose stack running for PostgreSQL and Elasticsearch.
