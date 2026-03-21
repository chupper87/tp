import json

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import get_database_url

_session_maker: async_sessionmaker | None = None


def _get_database_session() -> AsyncSession:
    global _session_maker
    if _session_maker is None:
        engine = create_async_engine(
            url=get_database_url(),
            echo=False,
            pool_size=10,
            max_overflow=5,
            future=True,
            json_serializer=lambda x: json.dumps(x, ensure_ascii=False),
        )
        _session_maker = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            expire_on_commit=False,
        )
    return _session_maker()


async def get_db():
    db = _get_database_session()
    try:
        yield db
    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()
