from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.app.core.settings import settings
from neo4j import AsyncGraphDatabase

# create the async engine
engine = create_async_engine(settings.DATABASE_URL, echo=True, future=True)

# create a configured "Session" class
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession
)


class DBConnections:
    neo4j_driver = None


db_connections = DBConnections()


# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# async def get_neo4j_driver():
#     neo4j_driver = AsyncGraphDatabase.driver(
#         settings.NEO4J_URI,
#         auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
#     )
#     yield neo4j_driver
# create the neo4j instance
# neo4j_driver = AsyncGraphDatabase.driver(
#     settings.NEO4J_URI,
#     auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
# )


# async def get_neo4j_session():
#     """
#     create a neo4j session for each request
#     close it when at the end of the request
#     """
#     async with neo4j_driver.session() as session:
#         yield session
