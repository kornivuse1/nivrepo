from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings


class Base(DeclarativeBase):
    pass


def get_engine():
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=False,
    )


def get_session_factory():
    engine = get_engine()
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def _add_user_ip_columns_if_missing(sync_conn):
    """Add created_ip and last_login_ip to users table if they don't exist (for existing DBs)."""
    for col in ["created_ip", "last_login_ip"]:
        try:
            sync_conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} VARCHAR(45)"))
        except Exception:
            pass


def _add_app_settings_allow_registration(sync_conn):
    """Add allow_registration to app_settings if missing (for existing DBs)."""
    try:
        sync_conn.execute(text("ALTER TABLE app_settings ADD COLUMN allow_registration INTEGER DEFAULT 1"))
    except Exception:
        pass


async def init_db():
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_add_user_ip_columns_if_missing)
        await conn.run_sync(_add_app_settings_allow_registration)


async def get_db():
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
