from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from core.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            logger.info("pgvector extension enabled")
        except Exception as e:
            logger.warning(f"pgvector extension not available: {e}")

        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")


async def close_db():
    await engine.dispose()
    logger.info("Database connections closed")
