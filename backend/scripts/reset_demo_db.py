"""
一键重置演示数据库。

SQLite（默认）：
  删除 lakesea.db 后重建表并写入基础种子数据。

达梦 DM8：
  按依赖顺序清空业务表后重新 seed_db。

用法：
  cd backend
  python -m scripts.reset_demo_db           # 重置 + 基础种子（用户/5资源）
  python -m scripts.reset_demo_db --full    # 重置 + 基础种子 + 完整演示流程
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings
from app.core.database import SessionLocal, engine, init_db
from app.core.db_info import is_dm8
from scripts.demo_seed_common import clear_business_data
from scripts.seed_db import seed as seed_basic
from scripts.schema_migrate import ensure_schema
from scripts.seed_demo_flow import seed_demo_flow


def _sqlite_db_path(database_url: str) -> Path | None:
    if not database_url.startswith("sqlite"):
        return None
    # sqlite:///./lakesea.db or sqlite:///path/to/db
    raw = database_url.replace("sqlite:///", "", 1)
    path = Path(raw)
    if not path.is_absolute():
        path = BACKEND_ROOT / path
    return path


def reset_sqlite(full_demo: bool) -> None:
    settings = get_settings()
    db_path = _sqlite_db_path(settings.database_url)
    if db_path is None:
        raise RuntimeError("无法解析 SQLite 路径")

    engine.dispose()
    recreated = False
    if db_path.exists():
        try:
            os.remove(db_path)
            recreated = True
            print(f"已删除 {db_path}")
        except OSError as exc:
            print(f"无法删除数据库文件（后端可能正在运行），改为清空表：{exc}")

    if recreated:
        ensure_schema()
    else:
        db = SessionLocal()
        try:
            clear_business_data(db)
            print("SQLite 业务表已清空。")
        finally:
            db.close()
        ensure_schema()

    seed_basic()
    print("基础种子数据已写入（5 角色 / 5 资源）。")

    if full_demo:
        seed_demo_flow(skip_basic=True)
    else:
        print("提示：运行 python -m scripts.seed_demo_flow 可生成完整演示流程数据。")


def reset_dm8(full_demo: bool) -> None:
    ensure_schema()
    db = SessionLocal()
    try:
        clear_business_data(db)
        print("达梦业务表已清空。")
    finally:
        db.close()

    seed_basic()
    print("基础种子数据已写入。")
    if full_demo:
        seed_demo_flow(skip_basic=True)


def reset(full_demo: bool = False) -> None:
    settings = get_settings()
    if is_dm8(settings.database_url):
        reset_dm8(full_demo)
    else:
        reset_sqlite(full_demo)


def main() -> None:
    parser = argparse.ArgumentParser(description="重置演示数据库")
    parser.add_argument(
        "--full",
        action="store_true",
        help="同时生成完整演示流程（10资源/3预约/归档试验/传感器/告警/AI）",
    )
    args = parser.parse_args()
    reset(full_demo=args.full)
    print("重置完成。")


if __name__ == "__main__":
    main()
