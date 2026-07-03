#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR=/workspace
LOGITEST_API_VENV="$ROOT_DIR/logitest-ai/apps/api/.venv"

export LOGITEST_DATABASE_URL="${LOGITEST_DATABASE_URL:-postgresql://logitest:logitest@postgres:5432/logitest_ai}"
export SHOPLITE_DATABASE_URL="${SHOPLITE_DATABASE_URL:-postgresql://shoplite:shoplite@postgres:5432/shoplite?schema=public}"
export POSTGRES_ADMIN_URL="${POSTGRES_ADMIN_URL:-}"
export ELASTICSEARCH_URL="${ELASTICSEARCH_URL:-http://elasticsearch:9200}"
export DEMO_LOG_INDEX="${DEMO_LOG_INDEX:-logitest-demo-logs}"
export SHOPLITE_LOG_INDEX="${SHOPLITE_LOG_INDEX:-logitest-demo-logs}"
export SHOPLITE_LOG_PATH="${SHOPLITE_LOG_PATH:-$ROOT_DIR/shoplite/server/logs/request-logs.jsonl}"
export STAGING_API_BASE_URL="${STAGING_API_BASE_URL:-http://localhost:4000}"
export NEXT_PUBLIC_API_BASE_URL="${NEXT_PUBLIC_API_BASE_URL:-http://localhost:8000}"
export VITE_API_BASE_URL="${VITE_API_BASE_URL:-http://localhost:4000}"
export CLIENT_ORIGIN="${CLIENT_ORIGIN:-http://localhost:5173}"
export JWT_SECRET="${JWT_SECRET:-shoplite-dev-secret}"
export ENVIRONMENT="${ENVIRONMENT:-production-demo}"
export ENABLE_PAYMENT_REGRESSION_BUG="${ENABLE_PAYMENT_REGRESSION_BUG:-false}"
export ENABLE_ELASTICSEARCH_LOGGING="${ENABLE_ELASTICSEARCH_LOGGING:-true}"

log() {
  printf '[logitest-stack] %s\n' "$*"
}

wait_for_postgres() {
  local url="$1"
  local name="$2"
  log "Waiting for PostgreSQL database: $name"
  until pg_isready -d "$url" >/dev/null 2>&1; do
    sleep 2
  done
}

ensure_postgres_databases() {
  if [[ -z "$POSTGRES_ADMIN_URL" ]]; then
    return
  fi

  wait_for_postgres "$POSTGRES_ADMIN_URL" postgres
  log "Ensuring LogiTest and ShopLite PostgreSQL roles/databases exist"
  psql "$POSTGRES_ADMIN_URL" -v ON_ERROR_STOP=1 <<'SQL'
DO
$$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'logitest') THEN
      CREATE ROLE logitest LOGIN PASSWORD 'logitest';
   END IF;

   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'shoplite') THEN
      CREATE ROLE shoplite LOGIN PASSWORD 'shoplite';
   END IF;
END
$$;

SELECT 'CREATE DATABASE logitest_ai OWNER logitest'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'logitest_ai')\gexec

SELECT 'CREATE DATABASE shoplite OWNER shoplite'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'shoplite')\gexec
SQL
}

wait_for_elasticsearch() {
  log "Waiting for Elasticsearch"
  until curl -fsS "$ELASTICSEARCH_URL/_cluster/health" >/dev/null 2>&1; do
    sleep 2
  done
}

shutdown() {
  log "Shutting down child processes"
  kill "${PIDS[@]:-}" >/dev/null 2>&1 || true
}
trap shutdown EXIT INT TERM

mkdir -p "$ROOT_DIR/shoplite/server/logs" "$ROOT_DIR/logitest-ai/generated-tests"
touch "$SHOPLITE_LOG_PATH"

ensure_postgres_databases
wait_for_postgres "$LOGITEST_DATABASE_URL" logitest_ai
wait_for_postgres "$SHOPLITE_DATABASE_URL" shoplite
wait_for_elasticsearch

log "Applying LogiTest AI database migrations"
for migration in "$ROOT_DIR"/logitest-ai/database/migrations/*.sql; do
  psql "$LOGITEST_DATABASE_URL" -v ON_ERROR_STOP=1 -f "$migration"
done

log "Applying ShopLite Prisma migrations and seed data"
(
  cd "$ROOT_DIR/shoplite/server"
  DATABASE_URL="$SHOPLITE_DATABASE_URL" npm run prisma:deploy
  DATABASE_URL="$SHOPLITE_DATABASE_URL" npm run seed
)

PIDS=()

log "Starting ShopLite API on :4000"
(
  cd "$ROOT_DIR/shoplite/server"
  DATABASE_URL="$SHOPLITE_DATABASE_URL" \
    PORT=4000 \
    npm start
) &
PIDS+=("$!")

log "Starting ShopLite frontend on :5173"
(
  cd "$ROOT_DIR/shoplite/client"
  npm run dev -- --host 0.0.0.0
) &
PIDS+=("$!")

log "Starting LogiTest AI API on :8000"
(
  cd "$ROOT_DIR/logitest-ai/apps/api"
  PATH="$LOGITEST_API_VENV/bin:$PATH" \
    DATABASE_URL="$LOGITEST_DATABASE_URL" \
    API_PORT=8000 \
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
) &
PIDS+=("$!")

log "Starting LogiTest AI dashboard on :3000"
(
  cd "$ROOT_DIR/logitest-ai"
  NODE_ENV=development npm run dev --workspace web -- --hostname 0.0.0.0
) &
PIDS+=("$!")

wait -n "${PIDS[@]}"
