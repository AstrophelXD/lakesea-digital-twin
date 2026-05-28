from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.user import SysRole, SysUser, SysUserRole


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[SysUser]:
        return self.db.get(SysUser, user_id)

    def get_by_username(self, username: str) -> Optional[SysUser]:
        stmt = select(SysUser).where(
            SysUser.username == username,
            SysUser.is_deleted == 0,
        )
        return self.db.scalar(stmt)

    def get_role_codes(self, user_id: int) -> List[str]:
        stmt = (
            select(SysRole.role_code)
            .join(SysUserRole, SysUserRole.role_id == SysRole.id)
            .where(SysUserRole.user_id == user_id)
        )
        return list(self.db.scalars(stmt).all())

    def get_user_with_roles(self, user_id: int) -> Optional[SysUser]:
        stmt = (
            select(SysUser)
            .options(joinedload(SysUser.user_roles).joinedload(SysUserRole.role))
            .where(SysUser.id == user_id, SysUser.is_deleted == 0)
        )
        return self.db.scalar(stmt)
