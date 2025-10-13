



from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker
)

from neo4j import AsyncGraphDatabase
from neo4j._async.driver import AsyncDriver
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

from src.app.core.config import Settings, settings
from src.app.models.base import Base


class DatabaseManager:

    def __init__(self, settings: Settings):
        self.settings = settings
        self._sql_engine: Optional[AsyncEngine] = None
        self._neo4j_driver: Optional[AsyncDriver] = None
        self._session_local = None

    @property
    def sql_engine(self) -> AsyncEngine:
        if self._sql_engine is None:
            self._sql_engine = create_async_engine(
                self.settings.DATABASE_URL,
                echo=self.settings.is_testing,
                future=True
            )
        return self._sql_engine


    @property
    def _get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_local is None:
            self._session_local = async_sessionmaker(
                autocommit=False,
                expire_on_commit=False,
                bind=self.sql_engine,
                class_=AsyncSession,
            )
        return self._session_local

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        session_factory = self._get_session_factory
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    @property
    def neo4j_driver(self) -> AsyncDriver:
        if self._neo4j_driver is None:
            self._neo4j_driver = AsyncGraphDatabase.driver(
                self.settings.NEO4J_URI,
                auth=(self.settings.NEO4J_USER, self.settings.NEO4J_PASSWORD)
            )
        return self._neo4j_driver

    async def initialize(self):
        try:
            await self.neo4j_driver.verify_connectivity()
        except Exception as e:
            raise RuntimeError(f"Neo4j driver connection failed: {e}")

    async def close(self):
        """Close all the database connection."""
        if self._sql_engine:
            await self._sql_engine.dispose()
        if self._neo4j_driver:
            await self.neo4j_driver.close()

    async def create_all_tables(self, base: Base):
        """create all tables."""
        async with self.sql_engine.begin() as conn:
            await conn.run_sync(base.metadata.create_all)
        # TODO: should I create the neo4j as well?

    async def drop_all_tables(self, base: Base):
        """drop all tables."""
        async with self.sql_engine.begin() as conn:
            await conn.run_sync(base.metadata.drop_all)


db_manager = DatabaseManager(settings)
