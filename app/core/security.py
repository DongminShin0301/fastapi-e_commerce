from datetime import datetime, timezone, timedelta

import jwt
from fastapi import HTTPException, status

from app.constants.role import Role
from app.core.config import ACCESS_TOKEN_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRED_TIME_MINUTES, TOKEN_ISSUER, REFRESH_TOKEN_EXPIRED_TIME_DAYS, \
    REFRESH_TOKEN_SECRET
from app.core.types.Payload import Payload, UserPayload
from app.schemas.user import UserData


def create_access_token(user: UserData):
    expired_at = datetime.now(tz=timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRED_TIME_MINUTES)
    payload = {
        "sub": str(user.id),
        "user": {
            "email": user.email,
            "role": user.role.name
        },
        "exp": expired_at,
        "iss": TOKEN_ISSUER,
        "iat": datetime.now(tz=timezone.utc)
    }

    return jwt.encode(payload, ACCESS_TOKEN_SECRET, algorithm=JWT_ALGORITHM)


def verify_access_token(token: str) -> Payload:
    try:
        decoded = jwt.decode(token, ACCESS_TOKEN_SECRET, algorithms=JWT_ALGORITHM)
        return Payload(
            sub=int(decoded.get("sub")),
            user=UserPayload(email=decoded.get("user").get("email"),
                             role=Role(decoded.get("user").get("role"))),
            exp=datetime.fromtimestamp(int(decoded.get("exp")), tz=timezone.utc),
            iss=decoded.get("iss"),
            iat=datetime.fromtimestamp(int(decoded.get("iat")), tz=timezone.utc)
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


def create_refresh_token(user_id: int) -> str:
    expired_at = datetime.now(tz=timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRED_TIME_DAYS)
    payload = {
        "sub": str(user_id),
        "exp": expired_at,
        "iss": TOKEN_ISSUER,
        "iat": datetime.now(tz=timezone.utc)
    }

    return jwt.encode(payload, REFRESH_TOKEN_SECRET, algorithm=JWT_ALGORITHM)


def verify_refresh_token(token: str):
    try:
        return jwt.decode(token, REFRESH_TOKEN_SECRET, algorithms=JWT_ALGORITHM)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
