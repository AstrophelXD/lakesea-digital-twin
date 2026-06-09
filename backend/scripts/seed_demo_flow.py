"""
生成完整答辩演示数据。

前置：已执行 seed_db（5 角色用户 + 5 条基础资源）。

用法：
  cd backend
  python -m scripts.seed_demo_flow

生成内容：
  - 10 条资源设备（补全 5 条）
  - 3 条预约（已归档 / 待主任审批 / 草稿）
  - 1 条完整审批链 + 已归档试验任务
  - 80 点传感器 + 轨迹 + 3 条告警 + AI 报告
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select

from app.core.database import SessionLocal
from scripts.schema_migrate import ensure_schema
from app.models.reservation import ExpReservation
from scripts.demo_seed_common import (
    create_archived_demo,
    create_draft_demo,
    create_pending_director_demo,
    ensure_extra_resources,
    get_resource_map,
    get_user_map,
)
from scripts.seed_db import seed as seed_basic


def seed_demo_flow(skip_basic: bool = False) -> None:
    if not skip_basic:
        ensure_schema()
        seed_basic()

    db = SessionLocal()
    try:
        existing = db.scalar(
            select(ExpReservation).where(ExpReservation.reservation_no == "RSV-DEMO-ARCHIVED")
        )
        if existing:
            print("演示数据已存在（RSV-DEMO-ARCHIVED），跳过。请先运行 reset_demo_db。")
            return

        ensure_extra_resources(db)
        users = get_user_map(db)
        resources = get_resource_map(db)

        required_users = ("student01", "teacher01", "director01")
        for name in required_users:
            if name not in users:
                raise RuntimeError(f"缺少用户 {name}，请先运行 python -m scripts.seed_db")

        archived_res, archived_task = create_archived_demo(db, users, resources)
        pending_res = create_pending_director_demo(db, users, resources)
        draft_res = create_draft_demo(db, users, resources)
        db.commit()

        print("演示流程数据写入完成：")
        print(f"  - 资源设备：10 条（含基础 5 + 扩展 5）")
        print(f"  - 预约 1（已归档）：{archived_res.reservation_no} -> 任务 {archived_task.task_no}")
        print(f"  - 预约 2（待主任审批）：{pending_res.reservation_no}")
        print(f"  - 预约 3（草稿）：{draft_res.reservation_no}")
        print(f"  - 传感器/轨迹：80 点；告警：3 条；AI 报告：1 份")
        print("答辩可直接打开「试验归档」「AI 分析」演示历史数据。")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_flow()
