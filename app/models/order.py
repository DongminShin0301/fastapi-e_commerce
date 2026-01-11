from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import ForeignKey, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models import User
from ..constants.order_status import OrderStatus

if TYPE_CHECKING:
    from .order_item import OrderItem


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    shipping_address: Mapped[str] = mapped_column(nullable=False)

    total_price: Mapped[int] = mapped_column(nullable=False)

    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    user: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship()

    def calculate_total_price(self):
        return sum(item.order_price * item.quantity for item in self.items)
