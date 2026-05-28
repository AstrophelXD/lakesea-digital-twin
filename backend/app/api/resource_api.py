from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from app.core.deps import CurrentUser, DbSession, require_roles
from app.models.user import SysUser
from app.core.response import success
from app.repositories.user_repository import UserRepository
from app.schemas.resource_schema import ResourceCreate, ResourceStatusUpdate, ResourceUpdate
from app.services.resource_service import ResourceService

router = APIRouter(prefix="/api/resources", tags=["资源设备"])

MaintainerUser = Annotated[SysUser, Depends(require_roles("ADMIN", "MAINTAINER"))]
AdminUser = Annotated[SysUser, Depends(require_roles("ADMIN"))]
StatusUser = Annotated[SysUser, Depends(require_roles("ADMIN", "MAINTAINER", "DIRECTOR"))]


@router.get("")
def list_resources(
    db: DbSession,
    _: CurrentUser,
    resource_type: Optional[str] = Query(None, alias="resourceType"),
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
):
    result = ResourceService(db).list_resources(resource_type, status, keyword, page, page_size)
    return success(result.model_dump(by_alias=True))


@router.get("/{resource_id}")
def get_resource(resource_id: int, db: DbSession, _: CurrentUser):
    result = ResourceService(db).get_resource(resource_id)
    return success(result.model_dump(by_alias=True))


@router.post("")
def create_resource(
    payload: ResourceCreate,
    db: DbSession,
    _: MaintainerUser,
):
    result = ResourceService(db).create_resource(payload)
    return success(result.model_dump(by_alias=True))


@router.put("/{resource_id}")
def update_resource(
    resource_id: int,
    payload: ResourceUpdate,
    db: DbSession,
    _: MaintainerUser,
):
    result = ResourceService(db).update_resource(resource_id, payload)
    return success(result.model_dump(by_alias=True))


@router.put("/{resource_id}/status")
def update_resource_status(
    resource_id: int,
    payload: ResourceStatusUpdate,
    db: DbSession,
    _: StatusUser,
):
    result = ResourceService(db).update_status(resource_id, payload)
    return success(result.model_dump(by_alias=True))


@router.delete("/{resource_id}")
def delete_resource(
    resource_id: int,
    db: DbSession,
    _: AdminUser,
):
    ResourceService(db).delete_resource(resource_id)
    return success(message="资源已停用")
