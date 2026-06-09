"""SQLite 开发库结构补丁（旧库缺列时自动补齐）。"""

from __future__ import annotations

from sqlalchemy import inspect, text

from app.core.config import get_settings
from app.core.database import engine, init_db


def _sqlite_column_exists(table: str, column: str) -> bool:
    insp = inspect(engine)
    tables = insp.get_table_names()
    match = next((t for t in tables if t.upper() == table.upper()), None)
    if not match:
        return False
    cols = {c["name"].upper() for c in insp.get_columns(match)}
    return column.upper() in cols


def ensure_schema() -> None:
    settings = get_settings()
    if not settings.database_url.startswith("sqlite"):
        init_db()
        return

    init_db()

    patches = [
        ("AI_REPORT", "ANALYSIS_TYPE", 'ALTER TABLE "AI_REPORT" ADD COLUMN "ANALYSIS_TYPE" VARCHAR(50)'),
    ]
    with engine.begin() as conn:
        for table, column, ddl in patches:
            if not _sqlite_column_exists(table, column):
                try:
                    conn.execute(text(ddl))
                except Exception:
                    pass
