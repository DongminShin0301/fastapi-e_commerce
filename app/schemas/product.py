import decimal

from pydantic import Field

from app.schemas.base_schema import BaseSchema


class ProductBase(BaseSchema):
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(max_length=2000)
    price: int = Field(ge=100)
    quantity: int = Field(ge=1)


class ProductCreate(ProductBase):
    pass


class ProductData(ProductBase):
    id: int
