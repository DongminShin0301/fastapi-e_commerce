import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.session import get_session, Base
from app.main import app

TEST_DB_URL = "sqlite+aiosqlite:///:memory"
BASE_URL = "http://test/api/v1"


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    test_engine = create_async_engine(TEST_DB_URL,
                                      echo=True,
                                      connect_args={"check_same_thread": False},
                                      poolclass=StaticPool)

    async with test_engine.connect() as conn:
        async with conn.begin():
            await conn.run_sync(Base.metadata.create_all)

    yield test_engine

    async with test_engine.connect() as conn:
        async with conn.begin():
            await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_session(async_engine):
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def async_client(async_session):
    async def override_get_db():
        yield async_session

    app.dependency_overrides[get_session] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url=BASE_URL) as client:
        yield client

    app.dependency_overrides.clear()
