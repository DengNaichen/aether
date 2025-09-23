from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# read the .env file
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


# create the async engine
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# create a configured "Session" class
AsyncSessionLocal = sessionmaker(
    autocommit = False,
    autoflush = False,
    bind = engine,
    class_ = AsyncSession
)

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session