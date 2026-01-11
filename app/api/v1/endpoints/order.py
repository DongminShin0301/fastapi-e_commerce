from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from app.core.get_current_user import get_current_user
from app.db.session import get_session
from app.models import Cart, OrderItem, Order, CartItem
from app.schemas.order import OrderCreate, OrderItemResponse, OrderResponse
from app.schemas.pagination import PageParams, PaginationResponse
from app.schemas.user import UserData

router = APIRouter(prefix="/api/v1/order")


@router.post("", status_code=201, response_model=OrderResponse)
async def create_order(request: OrderCreate,
                       session: AsyncSession = Depends(get_session),
                       current_user: UserData = Depends(get_current_user)):
    stmt = (
        select(Cart)
        .where(Cart.user_id == current_user.id)
        .options(selectinload(Cart.items).selectinload(CartItem.product))

    )
    user_cart: Cart | None = await session.scalar(stmt)

    # 장바구니 검색
    if not user_cart:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="no user cart")
    if not user_cart.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="empty user cart")

    # 장바구니에 있는 아이템을 주문 리스트로 담기
    order_items: List[OrderItem] = []
    for cart_item in user_cart.items:
        # 재고 확인 todo: 동시성 문제 해결하기
        if cart_item.product.quantity < cart_item.quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"procduct_id {cart_item.product_id} insufficient quantity")
        # 재고 차감
        cart_item.product.quantity -= cart_item.quantity

        order_item = OrderItem(
            product_id=cart_item.product_id,
            order_price=cart_item.product.price,
            quantity=cart_item.quantity)
        order_items.append(order_item)

    # 장바구니 비우기
    user_cart.items = []

    # 주문 아이템으로 새로운 주문 생성
    new_order = Order(user_id=current_user.id,
                      shipping_address=request.shipping_address,
                      items=order_items)
    new_order.total_price = new_order.calculate_total_price()
    session.add(new_order)

    await session.commit()

    order_item_responses = [OrderItemResponse.model_validate(item) for item in new_order.items]

    return OrderResponse(id=new_order.id,
                         user_id=current_user.id,
                         status=new_order.status,
                         total_price=new_order.total_price,
                         shipping_address=new_order.shipping_address,
                         created_at=new_order.created_at,
                         items=order_item_responses)


@router.get("", status_code=200, response_model=PaginationResponse[OrderResponse])
async def get_order(page_params: PageParams = Depends(),
                    session: AsyncSession = Depends(get_session),
                    current_user: UserData = Depends(get_current_user)):
    stmt = (
        select(
            Order,
            func.count().over().label("total_count")
        )
        .where(Order.user_id == current_user.id)
        .offset((page_params.page - 1) * page_params.size)
        .limit(page_params.size)
    )
    result = await session.execute(stmt)
    result = result.all()

    return PaginationResponse(
        current_page=page_params.page,
        size=len(result),
        total_page=1,
        total_items=1,
        items=[OrderResponse.model_validate(row[0]) for row in result]
    )
