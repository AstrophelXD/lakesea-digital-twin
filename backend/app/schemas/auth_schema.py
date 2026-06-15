from typing import List, Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=6, max_length=50)
    real_name: str = Field(..., min_length=1, max_length=100, alias="realName")
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[str] = Field(None, max_length=100)

    model_config = {"populate_by_name": True}


class UserInfo(BaseModel):
    id: int
    username: str
    real_name: str = Field(serialization_alias="realName")
    phone: Optional[str] = None
    email: Optional[str] = None
    roles: List[str] = []

    model_config = {"populate_by_name": True, "from_attributes": True}


class LoginResponse(BaseModel):
    token: str
    user: UserInfo


class ProfileResponse(BaseModel):
    user: UserInfo
    menus: List[str] = []
