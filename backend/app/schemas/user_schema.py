from typing import List, Optional

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=50)
    real_name: str = Field(..., min_length=1, max_length=100, alias="realName")
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[str] = Field(None, max_length=100)
    role_code: str = Field(..., alias="roleCode")

    model_config = {"populate_by_name": True}


class UserUpdate(BaseModel):
    real_name: Optional[str] = Field(None, min_length=1, max_length=100, alias="realName")
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[str] = Field(None, max_length=100)
    role_code: Optional[str] = Field(None, alias="roleCode")

    model_config = {"populate_by_name": True}


class ResetPasswordRequest(BaseModel):
    password: str = Field(..., min_length=6, max_length=50)


class UserListItem(BaseModel):
    id: int
    username: str
    real_name: str = Field(serialization_alias="realName")
    phone: Optional[str] = None
    email: Optional[str] = None
    status: str
    roles: List[str] = []

    model_config = {"populate_by_name": True, "from_attributes": True}
