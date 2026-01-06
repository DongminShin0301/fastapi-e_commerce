from pydantic import BaseModel, EmailStr

from app.schemas.user import UserData


class UserSignin(BaseModel):
    email: EmailStr
    password: str


class UserSigninResponse(BaseModel):
    access_token: str
    refresh_token: str
