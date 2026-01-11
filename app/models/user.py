from typing import TYPE_CHECKING, List

from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column, deferred, relationship

from app.constants.role import Role
from app.db.session import Base

if TYPE_CHECKING:
    from .order import Order


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False, default=Role.USER)
    is_active: Mapped[bool] = mapped_column(default=True)

    orders: Mapped[List["Order"]] = relationship(back_populates="user")
