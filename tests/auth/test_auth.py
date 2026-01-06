import time

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.users import password_hash
from app.core.security import create_refresh_token
from app.models import User, RefreshToken


async def test_signin_success(async_client: AsyncClient, async_session: AsyncSession):
    test_user = User(email="test@example.com",
                     hashed_password=password_hash.hash("12345678"),
                     is_active=True)
    async_session.add(test_user)
    await async_session.flush()  # ID를 할당받기 위해 flush 실행

    json = {
        "email": test_user.email,
        "password": "12345678"
    }

    response = await async_client.post("/auth/signin", json=json)
    await async_session.commit()  # 테스트 데이터 확정

    assert response.status_code == 200
    assert response.cookies["access_token"] is not None
    assert response.cookies["refresh_token"] is not None

    # refresh token db 저장 검증

    result = await async_session.execute(select(RefreshToken).where(RefreshToken.user_id == test_user.id))
    result = result.scalar_one_or_none()

    assert result is not None
    assert result.token == response.cookies["refresh_token"]


async def test_refresh_token_success(async_client: AsyncClient, async_session: AsyncSession):
    # 테스트 유저, 토큰 저장
    test_user = User(email="test@example.com",
                     hashed_password=password_hash.hash("12345678"),
                     is_active=True)
    async_session.add(test_user)
    await async_session.flush()

    old_token = create_refresh_token(test_user.id)
    test_token = RefreshToken(user=test_user, token=old_token)

    async_session.add(test_token)
    await async_session.commit()
    await async_session.refresh(test_token)

    time.sleep(1)

    async_client.cookies = {"refresh_token": old_token}
    response = await async_client.post("/auth/refresh_token")

    assert response.status_code == 201
    assert response.cookies["access_token"] is not None
    assert response.cookies["refresh_token"] is not None
    assert response.cookies["refresh_token"] != old_token

    await async_session.refresh(test_token)
    assert test_token.token == response.cookies["refresh_token"]
