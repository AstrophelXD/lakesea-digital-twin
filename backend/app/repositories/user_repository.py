from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
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

    def get_role_by_code(self, role_code: str) -> Optional[SysRole]:
        return self.db.scalar(select(SysRole).where(SysRole.role_code == role_code))

    def list_users(
        self,
        keyword: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[SysUser], int]:
        stmt = select(SysUser).where(SysUser.is_deleted == 0)
        if keyword:
            stmt = stmt.where(
                or_(
                    SysUser.username.like(f"%{keyword}%"),
                    SysUser.real_name.like(f"%{keyword}%"),
                )
            )
        if status:
            stmt = stmt.where(SysUser.status == status)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = list(
            self.db.scalars(
                stmt.order_by(SysUser.id.asc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return items, total

    def set_user_role(self, user_id: int, role_id: int) -> None:
        links = list(
            self.db.scalars(select(SysUserRole).where(SysUserRole.user_id == user_id)).all()
        )
        for link in links:
            self.db.delete(link)
        self.db.add(SysUserRole(user_id=user_id, role_id=role_id))
        self.db.flush()
