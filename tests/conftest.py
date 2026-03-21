import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from api import app
from config import config
from database import get_db
from idp.core import AUTH_COOKIE_NAME, AuthenticationJWT
from idp.email_and_password.repo import hash_password
from models import Base, User


@pytest.fixture(scope="session", autouse=True)
def create_tables() -> Generator[None, None, None]:
    """Create all tables once before the test session, drop them after."""

    async def _create() -> None:
        engine = create_async_engine(config.TEST_DATABASE_URL.get_secret_value())
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    async def _drop() -> None:
        engine = create_async_engine(config.TEST_DATABASE_URL.get_secret_value())
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    asyncio.run(_create())
    yield
    asyncio.run(_drop())


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async session that rolls back all changes after each test.

    Uses join_transaction_mode="create_savepoint" so that calls to
    session.commit() inside application code don't actually commit to the
    database — they only release the current savepoint. The outer connection-level
    transaction is rolled back at the end of the test, leaving the DB clean.
    """
    engine = create_async_engine(config.TEST_DATABASE_URL.get_secret_value())
    async with engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(
            bind=conn,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            yield session
        finally:
            await session.close()
            await conn.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client with the real app and the test DB session injected."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def user(db: AsyncSession) -> User:
    """A regular (non-admin) test user."""
    u = User(
        email="user@example.com",
        hashed_password=hash_password("password123"),
        is_active=True,
        is_admin=False,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession) -> User:
    """An admin test user."""
    u = User(
        email="admin@example.com",
        hashed_password=hash_password("password123"),
        is_active=True,
        is_admin=True,
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


@pytest_asyncio.fixture
async def authenticated_client(client: AsyncClient, user: User) -> AsyncClient:
    """HTTP client authenticated as a regular user (JWT cookie set)."""
    jwt = AuthenticationJWT.create(user_id=user.id)
    client.cookies.set(AUTH_COOKIE_NAME, jwt.token)
    return client


@pytest_asyncio.fixture
async def admin_client(client: AsyncClient, admin_user: User) -> AsyncClient:
    """HTTP client authenticated as an admin user (JWT cookie set)."""
    jwt = AuthenticationJWT.create(user_id=admin_user.id)
    client.cookies.set(AUTH_COOKIE_NAME, jwt.token)
    return client
