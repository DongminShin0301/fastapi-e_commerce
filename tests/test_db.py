from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


async def test_db(async_session: AsyncSession):
    old_user = User(email="test@example.com", hashed_password="test")
    async_session.add(old_user)
    await async_session.commit()
    await async_session.refresh(old_user)

    result = await async_session.execute(select(User).where(User.email == old_user.email))
    result = result.scalar_one_or_none()

    print(f"user's email before update >> {result.email}")

    # update

    stmt = insert(User).values(email="test@example.com", hashed_password="test")
    stmt = stmt.on_conflict_do_update(index_elements=[User.email],
                                      set_={"hashed_password": "wow"})
    await async_session.execute(stmt)
    await async_session.refresh(old_user)

    print(f"user's email after update >> {old_user.hashed_password}")
