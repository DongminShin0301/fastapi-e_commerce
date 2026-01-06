from typing import List

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.product import ProductData


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)


class CartItemUpdate(BaseModel):
    quantity: int


class CartItemResponse(BaseModel):
    id: int
    product: ProductData
    quantity: int

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    id: int
    items: List[CartItemResponse]
    total_price: float = 0

    model_config = ConfigDict(from_attributes=True)
