from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from pwdlib import PasswordHash
from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.user import User
from app.schemas.user import UserCreate, UserSignupResponse, UserData

router = APIRouter(prefix="/api/v1/users", tags=["users"])

password_hash = PasswordHash.recommended()


@router.post("/signup", status_code=201)
async def user_signup(user_create: UserCreate,
                      session: AsyncSession = Depends(get_session)) -> UserSignupResponse:
    email = user_create.email
    password = user_create.password

    stmt = select(exists().where(User.email == email))
    is_exist_email = await session.scalar(stmt)
    if is_exist_email:
        raise HTTPException(status_code=400, detail="Email already exists")

    hashed_password = password_hash.hash(password)
    new_user: User = User(email=str(email), hashed_password=hashed_password)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    return UserSignupResponse(user=UserData.model_validate(new_user))


@router.get("")
async def test_api():
    return {
        "message": "Tomato"
    }
