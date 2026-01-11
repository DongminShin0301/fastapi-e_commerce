from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field, AliasPath

from app.constants.order_status import OrderStatus


class OrderCreate(BaseModel):
    shipping_address: str


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str = Field(validation_alias=AliasPath("product", "name"))
    order_price: int
    quantity: int

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: OrderStatus
    total_price: int
    shipping_address: str
    created_at: datetime
    items: List[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)
