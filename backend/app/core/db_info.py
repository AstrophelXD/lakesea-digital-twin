"""数据库类型识别与健康检查（SQLite / 达梦 DM8）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

CORE_TABLES = [
    "SYS_USER",
    "SYS_ROLE",
    "SYS_USER_ROLE",
    "LAB_RESOURCE",
    "EXP_RESERVATION",
    "EXP_RESERVATION_RESOURCE",
    "EXP_APPROVAL_LOG",
    "EXPERIMENT_TASK",
    "SENSOR_DATA",
    "SHIP_TRACK",
    "ALARM_RECORD",
    "EXPERIMENT_FILE",
    "AI_REPORT",
    "AI_CALL_LOG",
]


def get_database_type(database_url: str) -> str:
    lower = database_url.lower()
    if lower.startswith("sqlite"):
        return "SQLite"
    if lower.startswith("dm") or "dmpython" in lower:
        return "达梦 DM8"
    return "其他数据库"


def is_dm8(database_url: str) -> bool:
    return get_database_type(database_url) == "达梦 DM8"


@dataclass
class DbHealthResult:
    database_type: str
    connected: bool
    table_counts: dict[str, int]
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "databaseType": self.database_type,
            "connected": self.connected,
            "tableCounts": self.table_counts,
            "coreTableTotal": sum(self.table_counts.values()),
            "error": self.error,
        }


def check_db_health(engine: Engine, database_url: str) -> DbHealthResult:
    db_type = get_database_type(database_url)
    table_counts: dict[str, int] = {}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            inspector = inspect(engine)
            existing = {t.upper() for t in inspector.get_table_names()}
            for table in CORE_TABLES:
                if table in existing:
                    count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    table_counts[table] = int(count or 0)
                else:
                    table_counts[table] = -1
        return DbHealthResult(
            database_type=db_type,
            connected=True,
            table_counts=table_counts,
        )
    except SQLAlchemyError as exc:
        return DbHealthResult(
            database_type=db_type,
            connected=False,
            table_counts=table_counts,
            error=str(exc),
        )
