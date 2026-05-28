from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.resource import LabResource


class ResourceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, resource_id: int) -> Optional[LabResource]:
        return self.db.scalar(
            select(LabResource).where(
                LabResource.id == resource_id,
                LabResource.is_deleted == 0,
            )
        )

    def list_resources(
        self,
        resource_type: Optional[str] = None,
        status: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[LabResource], int]:
        stmt = select(LabResource).where(LabResource.is_deleted == 0)
        if resource_type:
            stmt = stmt.where(LabResource.resource_type == resource_type)
        if status:
            stmt = stmt.where(LabResource.status == status)
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(
                or_(
                    LabResource.resource_name.like(like),
                    LabResource.resource_code.like(like),
                )
            )
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = list(
            self.db.scalars(
                stmt.order_by(LabResource.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()
        )
        return items, total

    def create(self, resource: LabResource) -> LabResource:
        self.db.add(resource)
        self.db.flush()
        return resource

    def save(self) -> None:
        self.db.flush()
