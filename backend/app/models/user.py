from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SysUser(Base):
    __tablename__ = "SYS_USER"

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column("USERNAME", String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column("PASSWORD_HASH", String(200), nullable=False)
    real_name: Mapped[str] = mapped_column("REAL_NAME", String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column("PHONE", String(30))
    email: Mapped[Optional[str]] = mapped_column("EMAIL", String(100))
    status: Mapped[str] = mapped_column("STATUS", String(20), default="ACTIVE")
    create_time: Mapped[datetime] = mapped_column(
        "CREATE_TIME", DateTime, server_default=func.now()
    )
    update_time: Mapped[datetime] = mapped_column(
        "UPDATE_TIME", DateTime, server_default=func.now(), onupdate=func.now()
    )
    is_deleted: Mapped[int] = mapped_column("IS_DELETED", Integer, default=0)

    user_roles: Mapped[List["SysUserRole"]] = relationship(back_populates="user")


class SysRole(Base):
    __tablename__ = "SYS_ROLE"

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True, autoincrement=True)
    role_code: Mapped[str] = mapped_column("ROLE_CODE", String(50), unique=True, nullable=False)
    role_name: Mapped[str] = mapped_column("ROLE_NAME", String(100), nullable=False)
    create_time: Mapped[datetime] = mapped_column(
        "CREATE_TIME", DateTime, server_default=func.now()
    )
    update_time: Mapped[datetime] = mapped_column(
        "UPDATE_TIME", DateTime, server_default=func.now(), onupdate=func.now()
    )

    user_roles: Mapped[List["SysUserRole"]] = relationship(back_populates="role")


class SysUserRole(Base):
    __tablename__ = "SYS_USER_ROLE"

    id: Mapped[int] = mapped_column("ID", Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        "USER_ID", Integer, ForeignKey("SYS_USER.ID"), nullable=False
    )
    role_id: Mapped[int] = mapped_column(
        "ROLE_ID", Integer, ForeignKey("SYS_ROLE.ID"), nullable=False
    )

    user: Mapped["SysUser"] = relationship(back_populates="user_roles")
    role: Mapped["SysRole"] = relationship(back_populates="user_roles")
