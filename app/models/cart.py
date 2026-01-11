from typing import List, TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from ..db.session import Base

if TYPE_CHECKING:
    from .user import User
    from .cart_item import CartItem


class Cart(Base):
    __tablename__ = "carts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(column="users.id", ondelete="CASCADE"), unique=True)

    user: Mapped["User"] = relationship()
    items: Mapped[List["CartItem"]] = relationship(lazy="selectin", cascade="all, delete-orphan")
