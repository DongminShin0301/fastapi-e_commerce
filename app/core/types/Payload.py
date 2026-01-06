from datetime import datetime

from pydantic import BaseModel

from app.constants.role import Role


class UserPayload(BaseModel):
    email: str
    role: Role


class Payload(BaseModel):
    sub: int
    user: UserPayload
    exp: datetime
    iss: str
    iat: datetime
