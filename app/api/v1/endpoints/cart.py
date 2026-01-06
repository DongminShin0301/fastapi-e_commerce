import logging

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.get_current_user import get_current_user
from app.db.session import get_session
from app.models import Cart, Product, CartItem
from app.schemas.cart import CartItemCreate, CartResponse
from app.schemas.user import UserData

router = APIRouter(prefix="/api/v1/cart")


@router.post("/item", status_code=status.HTTP_201_CREATED)
async def add_cart_item(request: CartItemCreate,
                        session: AsyncSession = Depends(get_session),
                        current_user: UserData = Depends(get_current_user)):
    """Cart item 추가"""
    user_cart = await session.scalar(select(Cart).where(Cart.user_id == current_user.id))

    # 장바구니가 없으면 생성함
    if not user_cart:
        user_cart = Cart(user_id=current_user.id)
        session.add(user_cart)
        await session.flush()

    product = await session.scalar(select(Product).where(Product.id == request.product_id))
    if product is None:
        logging.error(f"product_id {request.product_id} is not found")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"product_id {request.product_id} is not found")

    if product.quantity < request.quantity:
        logging.error(f"product_id {request.product_id} current quantity: {product.quantity},\n "
                      f"request quantity: {request.quantity}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"product_id {request.product_id} current quantity: {product.quantity},\n "
                                   f"request quantity: {request.quantity}")

    # 이미 담긴 아이템인지 확인
    stmt_item = select(CartItem).where(CartItem.cart_id == user_cart.id,
                                       CartItem.product_id == request.product_id)
    existing_item = await session.scalar(stmt_item)

    # 이미 존재하는 항목이라면 수량만 증가
    if existing_item:
        existing_item.quantity += request.quantity
        session.add(existing_item)
    else:
        cart_item = CartItem(cart_id=user_cart.id,
                             product_id=request.product_id,
                             quantity=request.quantity)
        session.add(cart_item)

    await session.commit()


@router.get("", status_code=200, response_model=CartResponse)
async def get_cart(current_user: UserData = Depends(get_current_user),
                   session: AsyncSession = Depends(get_session)):
    stmt = (
        select(Cart)
        .options(selectinload(Cart.items))
        .where(Cart.user_id == current_user.id)
    )

    result = (await session.execute(stmt)).scalar_one_or_none()
    if not result:
        return CartResponse(id=-1, items=[], total_price=0)

    total_price = 0

    for item in result.items:
        total_price += (item.product.price * item.quantity)

    return CartResponse(id=result.id, items=result.items, total_price=total_price)
