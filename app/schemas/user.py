from pydantic import Field, EmailStr

from app.constants.role import Role
from app.schemas.base_schema import BaseSchema


class UserCreate(BaseSchema):
    email: EmailStr
    password: str = Field(min_length=8, max_length=50)


class UserData(BaseSchema):
    id: int
    email: str
    role: Role
    is_active: bool


class UserSignupResponse(BaseSchema):
    message: str = "user created successfully"
    user: UserData
