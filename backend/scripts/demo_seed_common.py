"""演示数据种子公共工具。"""

from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Iterable, List, Tuple

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.archive import AiCallLog, AiReport, ExperimentFile
from app.models.audit import SysOperationLog
from app.models.constants import (
    ALARM_DATA_SPIKE,
    ALARM_LOW_BATTERY,
    ALARM_NEAR_BOUNDARY,
    APPROVAL_APPROVED,
    ARCHIVED,
    DIRECTOR_APPROVAL,
    DRAFT,
    PENDING_DIRECTOR,
    POOL_HEIGHT,
    POOL_WIDTH,
    TASK_ARCHIVED,
    TEACHER_REVIEW,
)
from app.models.experiment import ExperimentTask
from app.models.monitor import AlarmRecord, SensorData, ShipTrack
from app.models.reservation import ExpApprovalLog, ExpReservation, ExpReservationResource
from app.models.resource import LabResource
from app.models.user import SysRole, SysUser, SysUserRole

# 业务表清空顺序（子表优先）
BUSINESS_TABLES = [
    AiCallLog,
    AiReport,
    ExperimentFile,
    SysOperationLog,
    AlarmRecord,
    ShipTrack,
    SensorData,
    ExperimentTask,
    ExpApprovalLog,
    ExpReservationResource,
    ExpReservation,
    LabResource,
    SysUserRole,
    SysUser,
    SysRole,
]

EXTRA_RESOURCES = [
    ("POOL-02", "拖曳水池 B", "POOL", "AVAILABLE", "试验场南区"),
    ("SHIP-M002", "模型船 M-002", "SHIP", "AVAILABLE", "水池码头"),
    ("RES-01", "阻力测量单元", "SENSOR", "AVAILABLE", "设备间"),
    ("CAM-02", "水下摄像头", "CAMERA", "AVAILABLE", "水池西侧"),
    ("PWR-01", "供电与数据采集单元", "SENSOR", "AVAILABLE", "控制室"),
]


def clear_business_data(db: Session) -> None:
    for model in BUSINESS_TABLES:
        db.execute(delete(model))
    db.commit()


def get_user_map(db: Session) -> dict[str, SysUser]:
    users = db.scalars(select(SysUser).where(SysUser.is_deleted == 0)).all()
    return {u.username: u for u in users}


def get_resource_map(db: Session) -> dict[str, LabResource]:
    items = db.scalars(select(LabResource).where(LabResource.is_deleted == 0)).all()
    return {r.resource_code: r for r in items}


def ensure_extra_resources(db: Session) -> None:
    for code, name, rtype, status, loc in EXTRA_RESOURCES:
        exists = db.scalar(select(LabResource).where(LabResource.resource_code == code))
        if exists is None:
            db.add(
                LabResource(
                    resource_code=code,
                    resource_name=name,
                    resource_type=rtype,
                    status=status,
                    location=loc,
                    is_deleted=0,
                )
            )
    db.commit()


def _gen_trajectory(
    start: datetime, count: int = 80, interval_sec: int = 1
) -> List[dict]:
    x, y, heading, speed = 10.0, 10.0, 45.0, 1.5
    roll, pitch, battery, resistance = 0.0, 0.0, 100.0, 30.0
    frames: List[dict] = []
    for i in range(count):
        rad = math.radians(heading)
        x += speed * 0.5 * math.cos(rad) + random.uniform(-0.08, 0.08)
        y += speed * 0.5 * math.sin(rad) + random.uniform(-0.08, 0.08)
        if x <= 0 or x >= POOL_WIDTH:
            heading = (180 - heading) % 360
            x = max(0.5, min(POOL_WIDTH - 0.5, x))
        if x < 2.5 and i == 25:
            battery = 15.0
        if i == 50:
            resistance = 52.0
        heading = (heading + random.uniform(-6, 6)) % 360
        speed = max(0.5, min(3.0, speed + random.uniform(-0.1, 0.1)))
        roll = max(-20, min(20, roll + random.uniform(-1.5, 1.5)))
        pitch = max(-10, min(10, pitch + random.uniform(-0.8, 0.8)))
        battery = max(8, battery - random.uniform(0.4, 0.9))
        resistance = max(12, min(58, resistance + random.uniform(-2, 2)))
        ts = start + timedelta(seconds=i * interval_sec)
        frames.append(
            {
                "timestamp": ts,
                "x": round(x, 2),
                "y": round(y, 2),
                "heading": round(heading, 2),
                "speed": round(speed, 2),
                "roll": round(roll, 2),
                "pitch": round(pitch, 2),
                "battery": round(battery, 2),
                "resistance": round(resistance, 2),
            }
        )
    return frames


def persist_experiment_series(
    db: Session, experiment_id: int, frames: Iterable[dict]
) -> None:
    for f in frames:
        db.add(
            SensorData(
                experiment_id=experiment_id,
                timestamp=f["timestamp"],
                position_x=Decimal(str(f["x"])),
                position_y=Decimal(str(f["y"])),
                speed=Decimal(str(f["speed"])),
                heading=Decimal(str(f["heading"])),
                roll=Decimal(str(f["roll"])),
                pitch=Decimal(str(f["pitch"])),
                battery=Decimal(str(f["battery"])),
                resistance=Decimal(str(f["resistance"])),
            )
        )
        db.add(
            ShipTrack(
                experiment_id=experiment_id,
                timestamp=f["timestamp"],
                position_x=Decimal(str(f["x"])),
                position_y=Decimal(str(f["y"])),
                heading=Decimal(str(f["heading"])),
            )
        )


def create_archived_demo(
    db: Session,
    users: dict[str, SysUser],
    resources: dict[str, LabResource],
) -> Tuple[ExpReservation, ExperimentTask]:
    """完整审批链 → 已归档试验，含传感器/轨迹/告警/AI 报告。"""
    student = users["student01"]
    teacher = users["teacher01"]
    director = users["director01"]

    start = datetime.now() - timedelta(days=3)
    end = start + timedelta(hours=2)
    exp_start = start + timedelta(hours=1)
    exp_end = exp_start + timedelta(minutes=90)
    archive_at = exp_end + timedelta(hours=1)

    reservation = ExpReservation(
        reservation_no="RSV-DEMO-ARCHIVED",
        exp_name="稳向板阻力对比试验（演示归档）",
        exp_type="阻力测试",
        applicant_id=student.id,
        teacher_id=teacher.id,
        start_time=start,
        end_time=end,
        status=ARCHIVED,
        purpose="对比有无稳向板条件下的阻力曲线",
        plan_summary="低速段 0.5–2.0 m/s，采样间隔 1 s",
        submit_time=start - timedelta(hours=2),
        teacher_review_by=teacher.id,
        teacher_review_time=start - timedelta(hours=1, minutes=30),
        teacher_review_comment="方案可行，同意提交主任审批",
        director_approved_by=director.id,
        director_approved_time=start - timedelta(hours=1),
        director_approval_comment="资源已协调，批准试验",
        is_deleted=0,
    )
    db.add(reservation)
    db.flush()

    pool = resources["POOL-01"]
    ship = resources["SHIP-M001"]
    db.add_all(
        [
            ExpReservationResource(
                reservation_id=reservation.id,
                resource_id=pool.id,
                resource_type=pool.resource_type,
                quantity=1,
                start_time=start,
                end_time=end,
                remark="主试验水池",
            ),
            ExpReservationResource(
                reservation_id=reservation.id,
                resource_id=ship.id,
                resource_type=ship.resource_type,
                quantity=1,
                start_time=start,
                end_time=end,
                remark="模型船 M-001",
            ),
        ]
    )
    db.add_all(
        [
            ExpApprovalLog(
                reservation_id=reservation.id,
                step_type=TEACHER_REVIEW,
                approver_id=teacher.id,
                result=APPROVAL_APPROVED,
                comment="方案可行",
                action_time=start - timedelta(hours=1, minutes=30),
            ),
            ExpApprovalLog(
                reservation_id=reservation.id,
                step_type=DIRECTOR_APPROVAL,
                approver_id=director.id,
                result=APPROVAL_APPROVED,
                comment="批准试验",
                action_time=start - timedelta(hours=1),
            ),
        ]
    )

    task = ExperimentTask(
        task_no="TASK-DEMO-ARCHIVED",
        reservation_id=reservation.id,
        exp_name=reservation.exp_name,
        status=TASK_ARCHIVED,
        actual_start_time=exp_start,
        actual_end_time=exp_end,
        archive_time=archive_at,
        operator_id=student.id,
        is_deleted=0,
    )
    db.add(task)
    db.flush()

    frames = _gen_trajectory(exp_start, count=80)
    persist_experiment_series(db, task.id, frames)

    alarm_specs = [
        (25, ALARM_LOW_BATTERY, "HIGH", "电池电量过低 (15%)"),
        (25, ALARM_NEAR_BOUNDARY, "MEDIUM", "模型船接近边界"),
        (50, ALARM_DATA_SPIKE, "MEDIUM", "阻力数据突变"),
    ]
    for idx, atype, level, message in alarm_specs:
        db.add(
            AlarmRecord(
                experiment_id=task.id,
                alarm_type=atype,
                alarm_level=level,
                alarm_message=message,
                handle_status="RESOLVED" if atype != ALARM_NEAR_BOUNDARY else "PENDING",
                handler_id=director.id if atype != ALARM_NEAR_BOUNDARY else None,
                handle_time=frames[idx]["timestamp"] + timedelta(minutes=5)
                if atype != ALARM_NEAR_BOUNDARY
                else None,
                handle_comment="已更换电池" if atype == ALARM_LOW_BATTERY else None,
                create_time=frames[idx]["timestamp"],
            )
        )

    summary = (
        "【试验概况】\n稳向板阻力对比试验已完成。\n\n"
        "【关键数据】\n采样点 80 个；最大速度约 2.1 m/s；最低电量 15%。\n\n"
        "【异常记录】\n共 3 条告警：低电量、近边界、阻力突变。"
    )
    analysis = (
        "【可能原因】\n近边界与阻力突变可能与操船控制有关。\n\n"
        "【改进建议】\n建议延长低速段采样并优化稳向板安装角度。"
    )
    db.add(
        AiReport(
            experiment_id=task.id,
            report_title=f"{reservation.exp_name} - 试验概况摘要",
            analysis_type="OVERVIEW",
            summary_text=summary,
            analysis_text=analysis,
            model_name="mock-local",
            generated_by=teacher.id,
            is_deleted=0,
        )
    )
    db.add(
        AiCallLog(
            experiment_id=task.id,
            analysis_type="OVERVIEW",
            model_name="mock-local",
            is_mock=1,
            success=1,
            duration_ms=320,
            token_used=None,
            called_by=teacher.id,
        )
    )
    return reservation, task


def create_pending_director_demo(
    db: Session,
    users: dict[str, SysUser],
    resources: dict[str, LabResource],
) -> ExpReservation:
    student = users["student01"]
    teacher = users["teacher01"]
    start = datetime.now() + timedelta(days=1)
    end = start + timedelta(hours=3)

    reservation = ExpReservation(
        reservation_no="RSV-DEMO-PENDING",
        exp_name="波浪载荷测试（待主任审批）",
        exp_type="波浪试验",
        applicant_id=student.id,
        teacher_id=teacher.id,
        start_time=start,
        end_time=end,
        status=PENDING_DIRECTOR,
        purpose="演示教师已通过、待主任审批的预约",
        submit_time=datetime.now() - timedelta(hours=3),
        teacher_review_by=teacher.id,
        teacher_review_time=datetime.now() - timedelta(hours=1),
        teacher_review_comment="教师审核通过，请主任审批",
        is_deleted=0,
    )
    db.add(reservation)
    db.flush()

    for code in ("POOL-02", "SHIP-M002"):
        res = resources[code]
        db.add(
            ExpReservationResource(
                reservation_id=reservation.id,
                resource_id=res.id,
                resource_type=res.resource_type,
                quantity=1,
                start_time=start,
                end_time=end,
            )
        )
    db.add(
        ExpApprovalLog(
            reservation_id=reservation.id,
            step_type=TEACHER_REVIEW,
            approver_id=teacher.id,
            result=APPROVAL_APPROVED,
            comment="教师审核通过",
            action_time=datetime.now() - timedelta(hours=1),
        )
    )
    return reservation


def create_draft_demo(
    db: Session,
    users: dict[str, SysUser],
    resources: dict[str, LabResource],
) -> ExpReservation:
    student = users["student01"]
    teacher = users["teacher01"]
    start = datetime.now() + timedelta(days=7)
    end = start + timedelta(hours=2)

    reservation = ExpReservation(
        reservation_no="RSV-DEMO-DRAFT",
        exp_name="操纵性试航（草稿演示）",
        exp_type="操纵性",
        applicant_id=student.id,
        teacher_id=teacher.id,
        start_time=start,
        end_time=end,
        status=DRAFT,
        purpose="供学生演示新建预约与提交",
        plan_summary="Z 形操船 3 组",
        is_deleted=0,
    )
    db.add(reservation)
    db.flush()

    for code in ("TOW-01", "CAM-01"):
        res = resources[code]
        db.add(
            ExpReservationResource(
                reservation_id=reservation.id,
                resource_id=res.id,
                resource_type=res.resource_type,
                quantity=1,
                start_time=start,
                end_time=end,
                remark="草稿资源明细",
            )
        )
    return reservation
