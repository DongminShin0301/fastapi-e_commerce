from fastapi import HTTPException
from fastapi.params import Cookie

from app.core.security import verify_access_token
from app.schemas.user import UserData


def get_current_user(access_token: str = Cookie(None)):
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Token missing in cookie"
        )

    payload = verify_access_token(access_token)

    return UserData(
        id=payload.sub,
        email=payload.user.email,
        role=payload.user.role,
        is_active=True
    )
