from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from config import settings


engine = create_async_engine(settings.db_url, echo=settings.debug)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    async with engine.begin() as conn:
        from db.models import Novel, Chapter, Character, DialogueLine, AudioRecord
        await conn.run_sync(Base.metadata.create_all)

    # Auto-migrate: add missing columns for SQLite (existing DBs)
    from sqlalchemy import inspect, text
    async with engine.begin() as conn:
        def add_columns(sync_conn):
            inspector = inspect(sync_conn)
            cols = {c["name"] for c in inspector.get_columns("characters")}
            if "age_group" not in cols:
                sync_conn.execute(text("ALTER TABLE characters ADD COLUMN age_group VARCHAR(32) DEFAULT '成年'"))
            if "gender" not in cols:
                sync_conn.execute(text("ALTER TABLE characters ADD COLUMN gender VARCHAR(8) DEFAULT '男'"))
        try:
            await conn.run_sync(add_columns)
        except Exception as e:
            print(f"Migration note: {e}")


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
