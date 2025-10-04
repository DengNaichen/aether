from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .config import settings

# create the async engine
engine = create_async_engine(settings.DATABASE_URL, echo=True, future=True)

# create a configured "Session" class
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession
)


# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
