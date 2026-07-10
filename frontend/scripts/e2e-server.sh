#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BACKEND_PORT="${E2E_BACKEND_PORT:-8100}"
FRONTEND_PORT="${E2E_FRONTEND_PORT:-3100}"
BACKEND_PID=""
E2E_FRONTEND="${E2E_FRONTEND:-/tmp/autoscience-e2e-frontend}"

free_port() {
  local port="$1"
  if command -v fuser >/dev/null 2>&1; then
    fuser -k "${port}/tcp" >/dev/null 2>&1 || true
  fi
}

sync_e2e_frontend() {
  local lock_hash
  lock_hash="$(md5sum "$ROOT/frontend/package-lock.json" | awk '{print $1}')"

  mkdir -p "$E2E_FRONTEND"
  rsync -a --delete \
    --exclude node_modules \
    --exclude .next \
    "$ROOT/frontend/" "$E2E_FRONTEND/"

  if [ ! -d "$E2E_FRONTEND/node_modules" ] || [ "$(cat "$E2E_FRONTEND/.lock-hash" 2>/dev/null || true)" != "$lock_hash" ]; then
    echo "Installing frontend dependencies for E2E..."
    (cd "$E2E_FRONTEND" && unset NODE_ENV && npm ci --silent)
    echo "$lock_hash" > "$E2E_FRONTEND/.lock-hash"
  fi
}

ensure_frontend_build() {
  unset NEXT_DIST_DIR

  cd "$ROOT/frontend"
  if [ -f .next/BUILD_ID ]; then
    FRONTEND_DIR="$ROOT/frontend"
    return
  fi

  echo "Building frontend for E2E (workspace)..."
  if NODE_ENV=production npm run build && [ -f .next/BUILD_ID ]; then
    FRONTEND_DIR="$ROOT/frontend"
    return
  fi

  echo "Workspace build incomplete; using /tmp E2E mirror..."
  sync_e2e_frontend
  cd "$E2E_FRONTEND"
  if [ ! -f .next/BUILD_ID ]; then
    echo "Building frontend for E2E (/tmp mirror)..."
    NODE_ENV=production npm run build
  fi
  FRONTEND_DIR="$E2E_FRONTEND"
}

free_port "$BACKEND_PORT"
free_port "$FRONTEND_PORT"

cd "$ROOT/backend"
export DATABASE_URL=sqlite+aiosqlite:///./e2e.db
export DATABASE_URL_SYNC=sqlite:///./e2e.db
export E2E_DB_PATH=./e2e.db
uv run python scripts/init_e2e_db.py
uv run uvicorn app.main:app --host 127.0.0.1 --port "$BACKEND_PORT" &
BACKEND_PID=$!
trap 'kill "$BACKEND_PID" 2>/dev/null || true' EXIT

for _ in $(seq 1 90); do
  if curl -sf "http://127.0.0.1:${BACKEND_PORT}/api/v1/health" >/dev/null; then
    break
  fi
  sleep 1
done

export API_URL="http://127.0.0.1:${BACKEND_PORT}"
ensure_frontend_build
cd "$FRONTEND_DIR"
export NODE_ENV=production
exec npm run start -- -p "$FRONTEND_PORT" -H 127.0.0.1