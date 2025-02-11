from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = "sqlite+aiosqlite:///./db/test.db"
os.makedirs(os.path.dirname(DATABASE_URL.split("sqlite+aiosqlite:///")[1]), exist_ok=True)

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)
Base = declarative_base()

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session
