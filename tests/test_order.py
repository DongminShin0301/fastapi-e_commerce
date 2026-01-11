import copy
from datetime import datetime
from typing import List

import pytest_asyncio
import rich
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from app.constants.order_status import OrderStatus
from app.constants.role import Role
from app.core.security import create_access_token
from app.models import User, Product, Cart, CartItem, OrderItem, Order
from app.schemas.user import UserData


@pytest_asyncio.fixture
async def setup(async_session: AsyncSession, async_client: AsyncClient):
    user = User(email="test@example.com", hashed_password="test", role=Role.USER, is_active=True)
    cart = Cart(user=user)
    product1 = Product(name="example product 1", description="example desc 1", price=10000, quantity=100)
    product2 = Product(name="example product 2", description="example desc 2", price=5000, quantity=100)
    product3 = Product(name="example product 3", description="example desc 3", price=20000, quantity=100)
    async_session.add(user)
    async_session.add(cart)
    async_session.add_all([product1, product2, product3])
    await async_session.flush()

    token = create_access_token(UserData.model_validate(user))
    async_client.cookies = {"access_token": token}

    return {"user": user, "cart": cart, "products": [product1, product2, product3]}


async def test_create_order_success(setup,
                                    async_client: AsyncClient,
                                    async_session: AsyncSession):
    # given
    user, cart, products = setup["user"], setup["cart"], setup["products"]
    products_quantity_snapshot = {p.id: p.quantity for p in products}  # 주문 전/후 상태 비교를 위해 상품 수량 스냅샷

    cart_item1 = CartItem(cart_id=cart.id, product_id=products[0].id, quantity=2)
    cart_item2 = CartItem(cart_id=cart.id, product_id=products[1].id, quantity=1)
    async_session.add_all([cart_item1, cart_item2])
    await async_session.flush()
    await async_session.refresh(cart)

    shipping_address_request = "My HOME ADDRESS STREET 100, ABC 501"
    json = {
        "shipping_address": shipping_address_request
    }

    # when
    response = await async_client.post("/order", json=json)

    # then
    data = response.json()

    order_stmt = (
        select(Order)
        .where(Order.user_id == user.id)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
    )
    order: Order | None = await async_session.scalar(order_stmt)

    expect_total_price = 0
    for order_item in order.items:
        expect_total_price += order_item.order_price * order_item.quantity

    # order response assertions
    assert response.status_code == 201
    assert data["user_id"] == user.id
    assert data["status"] == OrderStatus.PENDING.value
    assert data["total_price"] == expect_total_price
    assert len(data["items"]) == 2

    # order data assertions
    assert order is not None
    assert order.status == OrderStatus.PENDING
    assert order.shipping_address == shipping_address_request
    assert order.total_price == expect_total_price
    assert len(order.items) == 2

    # 재고가 올바르게 차감되었는가?
    for order_item in order.items:
        original_quantity = products_quantity_snapshot[order_item.product_id]
        assert order_item.product.quantity == original_quantity - order_item.quantity

    # 장바구니의 아이템들이 비워졌는가? todo: 개별 구매 가능 변경
    await async_session.refresh(cart)
    assert len(cart.items) == 0


# 재고 부족으로 주문 생성 실패
async def test_create_order_fail_out_of_stock(setup, async_client: AsyncClient, async_session: AsyncSession):
    user, cart, products = setup["user"], setup["cart"], setup["products"]
    cart_item1 = CartItem(cart_id=cart.id, product_id=products[0].id, quantity=10000)
    cart_item2 = CartItem(cart_id=cart.id, product_id=products[1].id, quantity=1)
    async_session.add_all([cart_item1, cart_item2])
    await async_session.flush()

    response = await async_client.post("/order", json={"shipping_address": "test"})
    data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "insufficient" in data["detail"]

    result = (await async_session.scalars(select(Order))).all()
    assert not result


# 비어있는 장바구니로 주문 생성 실패
async def test_create_order_fail_empty_cart(setup, async_client: AsyncClient, async_session: AsyncSession):
    user, cart, products = setup["user"], setup["cart"], setup["products"]

    await async_session.refresh(cart)
    assert len(cart.items) == 0

    response = await async_client.post("/order", json={"shipping_address": "test"})
    data = response.json()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "empty" in data["detail"]


# 주문시점의 가격 스냅샷 검증
async def test_order_price_snapshot(setup, async_client: AsyncClient, async_session: AsyncSession):
    """Product의 가격이 변경되어도 OrderItem의 가격은 구매당시인가?"""
    user, cart, products = setup["user"], setup["cart"], setup["products"]
    product1 = products[0]
    product2 = products[1]

    cart_item1 = CartItem(cart_id=cart.id, product_id=product1.id, quantity=2)
    cart_item2 = CartItem(cart_id=cart.id, product_id=product2.id, quantity=1)
    async_session.add_all([cart_item1, cart_item2])
    await async_session.flush()
    await async_session.refresh(cart)

    response = await async_client.post("/order", json={"shipping_address": "test"})

    # 여기서도 product 정보를 참조하므로 selectinload가 필요합니다.
    order_stmt = (
        select(Order)
        .where(Order.user_id == user.id)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
    )
    order: Order | None = await async_session.scalar(order_stmt)

    assert response.status_code == status.HTTP_201_CREATED
    assert order is not None

    # 가격 변동 (인덱싱 오류 수정 및 반영)
    product1.price += 1000
    product2.price += 1000
    await async_session.flush()

    for order_item in order.items:
        assert order_item.order_price == order_item.product.price - 1000


# 주문 리스트 받아오기
async def test_get_order_list(setup, async_client: AsyncClient, async_session: AsyncSession):
    user, cart, products = setup["user"], setup["cart"], setup["products"]
    product1 = products[0]
    product2 = products[1]
    order1 = Order(user_id=1, shipping_address="test")
    order2 = Order(user_id=1, shipping_address="test")

    order_item1 = OrderItem(order=order1, product_id=product1.id, order_price=product1.price, quantity=2)
    order_item2 = OrderItem(order=order1, product_id=product2.id, order_price=product2.price, quantity=4)
    order_item3 = OrderItem(order=order2, product_id=product1.id, order_price=product2.price, quantity=1)
    order_item4 = OrderItem(order=order2, product_id=product2.id, order_price=product2.price, quantity=1)
    order1.items = [order_item1, order_item2]
    order2.items = [order_item3, order_item4]
    order1.total_price = order1.calculate_total_price()
    order2.total_price = order2.calculate_total_price()
    async_session.add_all([order1, order2])
    await async_session.flush()

    response = await async_client.get("/order?page=1&size=10")
    data = response.json()

    order1 = data["items"][0]
    order2 = data["items"][1]

    assert data["size"] == 2
    assert order1["user_id"] == user.id and order2["user_id"] == user.id
