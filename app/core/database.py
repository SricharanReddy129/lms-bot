# app/core/database.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

# 1. The Connection Engine
# What it does: This acts as the physical connection manager between your app and Aiven.
engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# 2. The Session Factory
# What it does: A template that creates individual "workspaces" (sessions) for executing queries.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# 3. The Ingestion Function (FastAPI Dependency)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    What this does:
    This is the "Ingestion Function". Whenever a user hits an API endpoint, FastAPI will call 
    this function to get a database session.
    """
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()