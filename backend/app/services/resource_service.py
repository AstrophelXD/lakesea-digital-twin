from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.constants import DISABLED, RESOURCE_UNAVAILABLE
from app.models.resource import LabResource
from app.models.user import SysUser
from app.repositories.resource_repository import ResourceRepository
from app.services.audit_service import AuditService
from app.schemas.common import PageResult
from app.schemas.resource_schema import (
    ResourceCreate,
    ResourceOut,
    ResourceStatusUpdate,
    ResourceUpdate,
)


class ResourceService:
    def __init__(self, db: Session) -> None:
        self.repo = ResourceRepository(db)
        self.db = db

    def list_resources(
        self,
        resource_type: Optional[str] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PageResult[ResourceOut]:
        items, total = self.repo.list_resources(resource_type, status, keyword, page, page_size)
        return PageResult(
            items=[ResourceOut.model_validate(i) for i in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_resource(self, resource_id: int) -> ResourceOut:
        resource = self.repo.get_by_id(resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="资源不存在")
        return ResourceOut.model_validate(resource)

    def create_resource(self, payload: ResourceCreate, operator: SysUser) -> ResourceOut:
        from sqlalchemy import select

        dup = self.db.scalar(
            select(LabResource).where(
                LabResource.resource_code == payload.resource_code,
                LabResource.is_deleted == 0,
            )
        )
        if dup:
            raise HTTPException(status_code=400, detail="资源编码已存在")
        resource = LabResource(
            resource_code=payload.resource_code,
            resource_name=payload.resource_name,
            resource_type=payload.resource_type,
            status="AVAILABLE",
            location=payload.location,
            manager_id=payload.manager_id,
            description=payload.description,
            is_deleted=0,
        )
        self.repo.create(resource)
        self.db.commit()
        self.db.refresh(resource)
        AuditService(self.db).log_user(
            operator,
            "RESOURCE",
            "CREATE",
            target_type="Resource",
            target_id=resource.id,
            detail=resource.resource_name,
        )
        return ResourceOut.model_validate(resource)

    def update_resource(
        self, resource_id: int, payload: ResourceUpdate, operator: SysUser
    ) -> ResourceOut:
        resource = self.repo.get_by_id(resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="资源不存在")
        data = payload.model_dump(exclude_unset=True, by_alias=False)
        for k, v in data.items():
            if v is not None:
                setattr(resource, k, v)
        self.db.commit()
        self.db.refresh(resource)
        AuditService(self.db).log_user(
            operator,
            "RESOURCE",
            "UPDATE",
            target_type="Resource",
            target_id=resource.id,
            detail=resource.resource_name,
        )
        return ResourceOut.model_validate(resource)

    def update_status(
        self, resource_id: int, payload: ResourceStatusUpdate, operator: SysUser
    ) -> ResourceOut:
        resource = self.repo.get_by_id(resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="资源不存在")
        resource.status = payload.status
        self.db.commit()
        self.db.refresh(resource)
        AuditService(self.db).log_user(
            operator,
            "RESOURCE",
            "UPDATE",
            target_type="Resource",
            target_id=resource.id,
            detail=f"状态→{payload.status}",
        )
        return ResourceOut.model_validate(resource)

    def delete_resource(self, resource_id: int, operator: SysUser) -> None:
        resource = self.repo.get_by_id(resource_id)
        if not resource:
            raise HTTPException(status_code=404, detail="资源不存在")
        resource.status = DISABLED
        resource.is_deleted = 1
        self.db.commit()
        AuditService(self.db).log_user(
            operator,
            "RESOURCE",
            "DELETE",
            target_type="Resource",
            target_id=resource.id,
            detail=resource.resource_name,
        )

    def ensure_bookable(self, resource_id: int) -> LabResource:
        resource = self.repo.get_by_id(resource_id)
        if not resource:
            raise HTTPException(status_code=400, detail=f"资源 ID {resource_id} 不存在")
        if resource.status in RESOURCE_UNAVAILABLE:
            raise HTTPException(
                status_code=400,
                detail=f"资源「{resource.resource_name}」当前状态为 {resource.status}，不可预约",
            )
        return resource
