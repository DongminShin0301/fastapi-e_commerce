import pytest
from httpx import AsyncClient
from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.role import Role
from app.core.security import create_access_token
from app.schemas.user import UserData


@pytest.mark.asyncio
async def test_add_product(async_client: AsyncClient, async_session: AsyncSession):
    token = create_access_token(UserData(id=1, email="test@example.com", role=Role.USER, is_active=True))

    payload = {
        "name": "test product1",
        "description": "this is good product",
        "price": 10000,
        "quantity": 10
    }
    async_client.cookies = {"access_token": token}
    response = await async_client.post("/products", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert isinstance(data["id"], int)
    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]
    assert data["price"] == payload["price"]
    assert data["quantity"] == payload["quantity"]
