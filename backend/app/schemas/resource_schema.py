from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ResourceCreate(BaseModel):
    resource_code: str = Field(..., alias="resourceCode", max_length=50)
    resource_name: str = Field(..., alias="resourceName", max_length=100)
    resource_type: str = Field(..., alias="resourceType", max_length=50)
    location: Optional[str] = None
    manager_id: Optional[int] = Field(None, alias="managerId")
    description: Optional[str] = None

    model_config = {"populate_by_name": True}


class ResourceUpdate(BaseModel):
    resource_name: Optional[str] = Field(None, alias="resourceName")
    resource_type: Optional[str] = Field(None, alias="resourceType")
    location: Optional[str] = None
    manager_id: Optional[int] = Field(None, alias="managerId")
    description: Optional[str] = None

    model_config = {"populate_by_name": True}


class ResourceStatusUpdate(BaseModel):
    status: str
    comment: Optional[str] = None


class ResourceOut(BaseModel):
    id: int
    resource_code: str = Field(serialization_alias="resourceCode")
    resource_name: str = Field(serialization_alias="resourceName")
    resource_type: str = Field(serialization_alias="resourceType")
    status: str
    location: Optional[str] = None
    manager_id: Optional[int] = Field(None, serialization_alias="managerId")
    description: Optional[str] = None
    create_time: Optional[datetime] = Field(None, serialization_alias="createTime")

    model_config = {"from_attributes": True, "populate_by_name": True}
