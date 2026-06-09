from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession, require_roles
from app.core.response import success
from app.models.user import SysRole, SysUser, SysUserRole
from app.schemas.user_schema import ResetPasswordRequest, UserCreate, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["用户"])

AdminUser = Annotated[SysUser, Depends(require_roles("ADMIN"))]


@router.get("")
def list_users(
    db: DbSession,
    _: AdminUser,
    keyword: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
):
    result = UserService(db).list_users(keyword, status, page, page_size)
    return success(result.model_dump(by_alias=True))


@router.post("")
def create_user(payload: UserCreate, db: DbSession, current_user: AdminUser):
    result = UserService(db).create_user(payload, current_user)
    return success(result.model_dump(by_alias=True))


@router.put("/{user_id}")
def update_user(user_id: int, payload: UserUpdate, db: DbSession, current_user: AdminUser):
    result = UserService(db).update_user(user_id, payload, current_user)
    return success(result.model_dump(by_alias=True))


@router.post("/{user_id}/reset-password")
def reset_password(
    user_id: int,
    payload: ResetPasswordRequest,
    db: DbSession,
    current_user: AdminUser,
):
    UserService(db).reset_password(user_id, payload, current_user)
    return success(None, message="密码已重置")


@router.post("/{user_id}/disable")
def toggle_disable(user_id: int, db: DbSession, current_user: AdminUser):
    result = UserService(db).disable_user(user_id, current_user)
    return success(result.model_dump(by_alias=True))


@router.get("/teachers")
def list_teachers(db: DbSession, _: CurrentUser):
    stmt = (
        select(SysUser.id, SysUser.username, SysUser.real_name)
        .join(SysUserRole, SysUserRole.user_id == SysUser.id)
        .join(SysRole, SysRole.id == SysUserRole.role_id)
        .where(SysRole.role_code == "TEACHER", SysUser.is_deleted == 0, SysUser.status == "ACTIVE")
    )
    rows = db.execute(stmt).all()
    data = [
        {"id": r.id, "username": r.username, "realName": r.real_name}
        for r in rows
    ]
    return success(data)
