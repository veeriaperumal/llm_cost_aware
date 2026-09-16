from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config.settings import settings

db_url = settings.database_url

engine = create_async_engine(
    db_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


_checkpointer = None


async def get_checkpointer():
    """Initialize and return a PostgreSQL-backed LangGraph checkpointer or fallback to MemorySaver."""
    global _checkpointer
    if _checkpointer is None:
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

            conn_str = db_url.replace("postgresql+asyncpg://", "postgresql://")
            _checkpointer = AsyncPostgresSaver.from_conn_string(conn_str)
            await _checkpointer.setup()
        except (ImportError, Exception):
            from langgraph.checkpoint.memory import MemorySaver
            _checkpointer = MemorySaver()
    return _checkpointer


async def init_db():
    import app.models.db_models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    from app.seed_data import seed_if_empty
    await seed_if_empty()
