"""初始化种子数据（用户、角色）。用法：在 backend 目录下执行 python -m scripts.seed_db"""

from __future__ import annotations

import sys
from pathlib import Path

# 将 backend 目录加入 path
BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select

from app.core.database import SessionLocal, init_db
from app.core.security import hash_password
from app.models.resource import LabResource
from app.models.user import SysRole, SysUser, SysUserRole

ROLES = [
    ("ADMIN", "系统管理员"),
    ("DIRECTOR", "试验场主任"),
    ("TEACHER", "指导教师"),
    ("STUDENT", "学生/研究员"),
    ("MAINTAINER", "设备维护人员"),
]

USERS = [
    ("admin", "系统管理员", "ADMIN", "123456"),
    ("director01", "王主任", "DIRECTOR", "123456"),
    ("teacher01", "李老师", "TEACHER", "123456"),
    ("student01", "张三", "STUDENT", "123456"),
    ("maintainer01", "赵维护", "MAINTAINER", "123456"),
]


def seed() -> None:
    init_db()
    db = SessionLocal()
    try:
        role_map: dict[str, int] = {}
        for code, name in ROLES:
            existing = db.scalar(select(SysRole).where(SysRole.role_code == code))
            if existing:
                role_map[code] = existing.id
            else:
                role = SysRole(role_code=code, role_name=name)
                db.add(role)
                db.flush()
                role_map[code] = role.id

        for username, real_name, role_code, password in USERS:
            user = db.scalar(select(SysUser).where(SysUser.username == username))
            if user is None:
                user = SysUser(
                    username=username,
                    password_hash=hash_password(password),
                    real_name=real_name,
                    status="ACTIVE",
                    is_deleted=0,
                )
                db.add(user)
                db.flush()
            else:
                user.password_hash = hash_password(password)

            link = db.scalar(
                select(SysUserRole).where(
                    SysUserRole.user_id == user.id,
                    SysUserRole.role_id == role_map[role_code],
                )
            )
            if link is None:
                db.add(SysUserRole(user_id=user.id, role_id=role_map[role_code]))

        resources = [
            ("POOL-01", "拖曳水池 A", "POOL", "AVAILABLE", "试验场北区"),
            ("SHIP-M001", "模型船 M-001", "SHIP", "AVAILABLE", "水池码头"),
            ("IMU-01", "IMU 姿态传感器", "SENSOR", "AVAILABLE", "设备间"),
            ("CAM-01", "高速摄像头", "CAMERA", "AVAILABLE", "水池东侧"),
            ("TOW-01", "拖车设备", "TOWING", "AVAILABLE", "试验场北区"),
        ]
        for code, name, rtype, st, loc in resources:
            exists = db.scalar(
                select(LabResource).where(LabResource.resource_code == code)
            )
            if exists is None:
                db.add(
                    LabResource(
                        resource_code=code,
                        resource_name=name,
                        resource_type=rtype,
                        status=st,
                        location=loc,
                        is_deleted=0,
                    )
                )

        db.commit()
        print("种子数据写入完成。默认密码均为：123456")
        print("账号：admin / director01 / teacher01 / student01 / maintainer01")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
