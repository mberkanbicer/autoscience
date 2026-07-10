#!/usr/bin/env python3
"""Verify pgvector extension and paper_embeddings column on PostgreSQL."""

from __future__ import annotations

import os
import sys

from sqlalchemy import create_engine, inspect, text


def main() -> int:
    url = os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL", "")
    if not url.startswith("postgresql"):
        print("SKIP: set DATABASE_URL_SYNC to postgresql://...")
        return 0

    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "")

    engine = create_engine(url)
    with engine.connect() as conn:
        ext = conn.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        ).scalar_one_or_none()
        if ext is None:
            print("FAIL: pgvector extension not installed", file=sys.stderr)
            return 1

        columns = {c["name"] for c in inspect(engine).get_columns("paper_embeddings")}
        if "embedding_vector" not in columns:
            print("FAIL: paper_embeddings.embedding_vector column missing", file=sys.stderr)
            return 1

    print("OK: pgvector extension and embedding_vector column present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())