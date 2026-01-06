from math import ceil

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.get_current_user import get_current_user
from app.db.session import get_session
from app.models import Product
from app.schemas.pagination import PaginationResponse, PageParams
from app.schemas.product import ProductCreate, ProductData
from app.schemas.user import UserData
from app.utils.normalize_name import normalize_name

router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.post("", status_code=201)
async def add_product(request: ProductCreate,
                      session: AsyncSession = Depends(get_session),
                      user: UserData = Depends(get_current_user)) -> ProductData:
    normalized_name = normalize_name(request.name)
    stmt = select(Product).where(func.trim(Product.name) == normalized_name)
    result = (await session.execute(stmt)).scalar_one_or_none()

    if result is not None:
        raise HTTPException(status_code=409, detail="Already exist product name")

    new_product = Product(
        name=normalized_name,
        description=request.description,
        price=request.price,
        quantity=request.quantity
    )

    session.add(new_product)
    await session.commit()
    await session.refresh(new_product)

    return ProductData.model_validate(new_product)


@router.get("", status_code=200, response_model=PaginationResponse[ProductData])
async def get_products(params: PageParams = Depends(),
                       session: AsyncSession = Depends(get_session)):
    stmt = (
        select(Product,
               func.count().over().label("total_count")
               )
        .offset((params.page - 1) * params.size)
        .limit(params.size))

    result = (await session.execute(stmt)).all()

    if not result:
        raise HTTPException(status_code=400, detail="no more data")

    products = [row[0] for row in result]
    total_items = result[0][1]
    total_page = ceil(total_items / params.size)

    return PaginationResponse(
        current_page=params.page,
        size=len(products),
        total_page=total_page,
        total_items=total_items,
        items=products,
    )
