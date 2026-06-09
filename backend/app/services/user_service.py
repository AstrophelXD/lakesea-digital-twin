from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import SysUser
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.schemas.common import PageResult
from app.schemas.user_schema import (
    ResetPasswordRequest,
    UserCreate,
    UserListItem,
    UserUpdate,
)


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UserRepository(db)

    def _to_item(self, user: SysUser) -> UserListItem:
        roles = self.repo.get_role_codes(user.id)
        return UserListItem(
            id=user.id,
            username=user.username,
            real_name=user.real_name,
            phone=user.phone,
            email=user.email,
            status=user.status,
            roles=roles,
        )

    def list_users(
        self,
        keyword: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PageResult[UserListItem]:
        items, total = self.repo.list_users(keyword, status, page, page_size)
        return PageResult(
            items=[self._to_item(u) for u in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def create_user(self, payload: UserCreate, operator: SysUser) -> UserListItem:
        if self.repo.get_by_username(payload.username):
            raise HTTPException(status_code=400, detail="用户名已存在")
        role = self.repo.get_role_by_code(payload.role_code)
        if role is None:
            raise HTTPException(status_code=400, detail="角色不存在")
        user = SysUser(
            username=payload.username,
            password_hash=hash_password(payload.password),
            real_name=payload.real_name,
            phone=payload.phone,
            email=payload.email,
            status="ACTIVE",
            is_deleted=0,
        )
        self.db.add(user)
        self.db.flush()
        self.repo.set_user_role(user.id, role.id)
        self.db.commit()
        self.db.refresh(user)
        AuditService(self.db).log_user(
            operator,
            "USER",
            "CREATE",
            target_type="User",
            target_id=user.id,
            detail=f"{user.username} ({payload.role_code})",
        )
        return self._to_item(user)

    def update_user(self, user_id: int, payload: UserUpdate, operator: SysUser) -> UserListItem:
        user = self.repo.get_by_id(user_id)
        if user is None or user.is_deleted != 0:
            raise HTTPException(status_code=404, detail="用户不存在")
        if payload.real_name is not None:
            user.real_name = payload.real_name
        if payload.phone is not None:
            user.phone = payload.phone
        if payload.email is not None:
            user.email = payload.email
        if payload.role_code is not None:
            role = self.repo.get_role_by_code(payload.role_code)
            if role is None:
                raise HTTPException(status_code=400, detail="角色不存在")
            self.repo.set_user_role(user.id, role.id)
        self.db.commit()
        self.db.refresh(user)
        AuditService(self.db).log_user(
            operator,
            "USER",
            "UPDATE",
            target_type="User",
            target_id=user.id,
            detail=user.username,
        )
        return self._to_item(user)

    def reset_password(
        self, user_id: int, payload: ResetPasswordRequest, operator: SysUser
    ) -> None:
        user = self.repo.get_by_id(user_id)
        if user is None or user.is_deleted != 0:
            raise HTTPException(status_code=404, detail="用户不存在")
        user.password_hash = hash_password(payload.password)
        self.db.commit()
        AuditService(self.db).log_user(
            operator,
            "USER",
            "RESET_PASSWORD",
            target_type="User",
            target_id=user.id,
            detail=user.username,
        )

    def disable_user(self, user_id: int, operator: SysUser) -> UserListItem:
        user = self.repo.get_by_id(user_id)
        if user is None or user.is_deleted != 0:
            raise HTTPException(status_code=404, detail="用户不存在")
        if user.status == "DISABLED":
            user.status = "ACTIVE"
            action = "ENABLE"
        else:
            user.status = "DISABLED"
            action = "DISABLE"
        self.db.commit()
        self.db.refresh(user)
        AuditService(self.db).log_user(
            operator,
            "USER",
            action,
            target_type="User",
            target_id=user.id,
            detail=user.username,
        )
        return self._to_item(user)
