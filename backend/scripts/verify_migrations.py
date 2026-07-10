#!/usr/bin/env python3
"""Verify Alembic migrations apply cleanly on a fresh database.

Usage:
    cd backend && python scripts/verify_migrations.py
    cd backend && python scripts/verify_migrations.py --postgres

Exit codes:
    0 — migrations applied and schema checks passed
    1 — migration or verification failed
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

BACKEND_DIR = Path(__file__).resolve().parents[1]
EXPECTED_HEAD = "f6a7b8c9d0e1"

REQUIRED_TABLES = [
    "alembic_version",
    "projects",
    "ideas",
    "research_runs",
    "papers",
    "knowledge_notes",
    "manuscripts",
    "datasets",
    "users",
    "project_members",
    "comments",
    "review_proposals",
]

REQUIRED_COLUMNS: dict[str, list[str]] = {
    "research_runs": ["step_history", "current_phase", "cognitive_entropy"],
    "knowledge_notes": ["run_id"],
    "papers": ["references"],
}


def _run_alembic_upgrade(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def verify_database(sync_url: str, label: str) -> bool:
    env = os.environ.copy()
    env["DATABASE_URL"] = sync_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    env["DATABASE_URL_SYNC"] = sync_url

    print(f"[{label}] Running alembic upgrade head...")
    result = _run_alembic_upgrade(env)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        return False

    engine = create_engine(sync_url)
    inspector = inspect(engine)

    tables = set(inspector.get_table_names())
    missing_tables = [t for t in REQUIRED_TABLES if t not in tables]
    if missing_tables:
        print(f"[{label}] Missing tables: {missing_tables}", file=sys.stderr)
        return False

    with engine.connect() as conn:
        revision = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        if revision != EXPECTED_HEAD:
            print(
                f"[{label}] Expected head {EXPECTED_HEAD}, got {revision}",
                file=sys.stderr,
            )
            return False

    for table, columns in REQUIRED_COLUMNS.items():
        existing = {c["name"] for c in inspector.get_columns(table)}
        missing_cols = [c for c in columns if c not in existing]
        if missing_cols:
            print(f"[{label}] Table {table} missing columns: {missing_cols}", file=sys.stderr)
            return False

    print(f"[{label}] OK — head={revision}, tables={len(tables)}")
    return True


def verify_sqlite() -> bool:
    with tempfile.TemporaryDirectory(prefix="autoscience-migrate-") as tmp:
        db_path = Path(tmp) / "verify.db"
        sync_url = f"sqlite:///{db_path}"
        return verify_database(sync_url, "sqlite")


def verify_postgres(url: str) -> bool:
    return verify_database(url, "postgres")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify fresh DB migrations")
    parser.add_argument(
        "--postgres",
        action="store_true",
        help="Also verify against DATABASE_URL_SYNC or DATABASE_URL if PostgreSQL",
    )
    args = parser.parse_args()

    ok = verify_sqlite()

    if args.postgres:
        pg_url = os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL", "")
        if pg_url.startswith("postgresql"):
            if "+asyncpg" in pg_url:
                pg_url = pg_url.replace("+asyncpg", "")
            ok = verify_postgres(pg_url) and ok
        else:
            print("Skipping postgres — set DATABASE_URL_SYNC to a postgresql:// URL")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())