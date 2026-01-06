from typing import Annotated

from fastapi import APIRouter, HTTPException, Response
from fastapi.params import Depends, Cookie
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.users import password_hash
from app.core.security import create_access_token, create_refresh_token, verify_refresh_token
from app.db.session import get_session
from app.models import User, RefreshToken
from app.schemas.auth import UserSignin
from app.schemas.user import UserData

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/signin", status_code=200)
async def signin(request: UserSignin,
                 response: Response,
                 session: AsyncSession = Depends(get_session)):
    email = request.email
    password = request.password

    user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()

    unauthorize_exception = HTTPException(status_code=401, detail="Email or password is invalid")
    if user is None:
        raise unauthorize_exception

    verify = password_hash.verify(password, user.hashed_password)
    if not verify:
        raise unauthorize_exception

    access_token = create_access_token(UserData.model_validate(user))
    refresh_token = create_refresh_token(user.id)

    # upsert
    stmt = insert(RefreshToken).values(user_id=user.id, token=refresh_token)
    stmt = stmt.on_conflict_do_update(index_elements=[RefreshToken.user_id],
                                      set_={"token": refresh_token})
    await session.execute(stmt)
    await session.commit()

    response.set_cookie(key="access_token", value=access_token, httponly=True, samesite="lax")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, samesite="lax")

    return UserData.model_validate(user)


@router.post("/refresh_token", status_code=201)
async def generate_refresh_token(response: Response,
                                 refresh_token: str | None = Cookie(default=None),
                                 session: AsyncSession = Depends(get_session)):
    if refresh_token is None:
        raise HTTPException(status_code=400, detail="refresh token is required")

    payload = verify_refresh_token(refresh_token)
    user_id = int(payload.get("sub"))

    stmt = select(RefreshToken).where(RefreshToken.user_id == user_id).options(selectinload(RefreshToken.user))
    result = (await session.execute(stmt)).scalar_one_or_none()

    if result is None or result.token != refresh_token:
        raise HTTPException(status_code=401, detail="invalid jwt")

    new_access_token = create_access_token(UserData.model_validate(result.user))
    new_refresh_token = create_refresh_token(user_id)

    stmt = insert(RefreshToken).values(user_id=user_id, token=new_refresh_token)
    stmt = stmt.on_conflict_do_update(index_elements=[RefreshToken.user_id],
                                      set_={"token": new_refresh_token})
    await session.execute(stmt)
    await session.commit()

    response.set_cookie(key="access_token", value=new_access_token, httponly=True, samesite="lax")
    response.set_cookie(key="refresh_token", value=new_refresh_token, httponly=True, samesite="lax")
