import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


@pytest.mark.asyncio
async def test_user_signup(async_client: AsyncClient, async_session: AsyncSession):
    payload = {
        "email": "user10000@example.com",
        "password": "12345678"
    }

    response = await async_client.post("/users/signup", json=payload)

    # assertions
    data = response.json()

    assert response.status_code == 201
    assert data["message"] == "user created successfully"
    assert "user" in data
    assert isinstance(data["user"]["id"], int)
    assert data["user"]["email"] == "user10000@example.com"
    assert data["user"]["is_active"] is True

    stmt = select(User).where(User.email == payload["email"])
    result = await async_session.execute(stmt)

    db_user = result.scalars().first()
    assert db_user is not None
    assert db_user.email == payload["email"]
    assert db_user.id == data['user']['id']
