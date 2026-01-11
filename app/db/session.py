import os

from click import echo
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import MappedAsDataclass, DeclarativeBase

load_dotenv()


class Base(DeclarativeBase):
    pass


DATABASE_URL = os.getenv("DATABASE_URL")
# Base = declarative_base()

engine = create_async_engine(url=DATABASE_URL,
                             pool_pre_ping=True,
                             pool_size=20,
                             pool_timeout=3600,
                             # echo=True,
                             connect_args={"check_same_thread": False})

AsyncSessionLocal = async_sessionmaker(bind=engine,
                                       autocommit=False,
                                       autoflush=False,
                                       expire_on_commit=False)


async def get_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()


async def create_db_and_tables():
    async with engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db_connection():
    await engine.dispose()
