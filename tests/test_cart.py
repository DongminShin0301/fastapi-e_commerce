import logging
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.constants.role import Role
from app.core.security import create_access_token
from app.models import User, Product, CartItem, Cart
from app.schemas.user import UserData


@pytest_asyncio.fixture(autouse=True)
async def setup(async_session: AsyncSession,
                async_client: AsyncClient):
    logging.info("test_cart setup")

    user = User(id=1,
                email="test@example.com",
                hashed_password="test",
                role=Role.USER,
                is_active=True)

    async_session.add(user)
    await async_session.flush()

    token = create_access_token(UserData.model_validate(user))
    async_client.cookies = {"access_token": token}
    product1 = Product(name='test product 1', description="desc 1", quantity=10, price=10000)
    product2 = Product(name='test product 2', description="desc 2", quantity=1, price=20000)
    product3 = Product(name='test product 3', description="desc 3", quantity=0, price=30000)
    async_session.add(product1)
    async_session.add(product2)
    async_session.add(product3)
    await async_session.flush()

    return {"user": user, "products": [product1, product2, product3]}


async def test_add_cart_item_successfully(setup,
                                          async_session: AsyncSession,
                                          async_client: AsyncClient):
    user = setup["user"]
    products = setup["products"]
    json = {
        "product_id": 1,
        "quantity": 1,
    }

    response = await async_client.post("/cart/item", json=json)
    # data = response.json()

    cart: Cart | None = await async_session.scalar(select(Cart).where(Cart.user_id == user.id))
    assert response.status_code == status.HTTP_201_CREATED
    assert len(cart.items) == 1
    assert cart.items[0].id == products[0].id


async def test_add_cart_item_already_exist(setup,
                                           async_session: AsyncSession,
                                           async_client: AsyncClient):
    """이미 장바구니에 존재하는 product인 경우 수량만 증가"""
    user, products = setup["user"], setup["products"]
    cart = Cart(user_id=user.id)
    async_session.add(cart)
    cart.items.append(CartItem(product_id=products[0].id, quantity=1))
    await async_session.flush()

    json = {"product_id": products[0].id, "quantity": 2}
    response = await async_client.post("/cart/item", json=json)

    cart_result = await async_session.scalar(select(Cart).where(Cart.user_id == user.id))

    assert response.status_code == 201
    assert len(cart_result.items) == 1
    assert cart_result.items[0].product_id == products[0].id
    assert cart_result.items[0].quantity == 3


async def test_add_cart_item_insufficient_quantity(setup, async_client: AsyncClient):
    """상품의 재고보다 많은 양을 장바구니에 담으려는 경우 예외발생"""
    user, products = setup["user"], setup["products"]

    json = {"product_id": 2, "quantity": 1000}
    response = await async_client.post("/cart/item", json=json)
    data = response.json()

    assert response.status_code == 400


async def test_get_cart(setup,
                        async_client: AsyncClient,
                        async_session: AsyncSession):
    user, products = setup["user"], setup["products"]
    cart = Cart(id=1,
                user=user,
                items=[CartItem(cart_id=1, product_id=products[0].id, quantity=2),
                       CartItem(cart_id=1, product_id=products[1].id, quantity=1)])
    async_session.add(cart)
    await async_session.flush()

    response = await async_client.get("/cart")

    data = response.json()

    assert response.status_code == 200
    # assert data["user_id"] == user.id
    assert len(data["items"]) == 2
    assert data["items"][0]["id"] == products[0].id
