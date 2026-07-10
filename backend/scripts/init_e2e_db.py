"""Initialize SQLite schema for E2E from SQLAlchemy models (not Alembic)."""

import asyncio
import os
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine

from app.models.base import Base
import app.models  # noqa: F401 — register all models


async def main() -> None:
    db_path = os.environ.get("E2E_DB_PATH", "./e2e.db")
    if db_path != ":memory:":
        Path(db_path).unlink(missing_ok=True)
    url = f"sqlite+aiosqlite:///{db_path}"
    engine = create_async_engine(url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print(f"E2E database initialized at {db_path}")


if __name__ == "__main__":
    asyncio.run(main())