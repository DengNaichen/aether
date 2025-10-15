import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession as Neo4jAsyncSession
from redis.asyncio import Redis
import redis.asyncio as aioredis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.app.core.config import Settings, settings
from src.app.models.base import Base


class DatabaseManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._sql_engine: Optional[AsyncEngine] = None
        self._neo4j_driver: Optional[AsyncDriver] = None
        self._session_local = None
        self._redis_client: Optional[Redis] = None

    # ==================== PostgreSQL ====================
    @property
    def sql_engine(self) -> AsyncEngine:
        """
        Lazy initialization of SQL engine.
        """
        if self._sql_engine is None:
            self._sql_engine = create_async_engine(
                self.settings.DATABASE_URL,
                echo=self.settings.is_testing,
                future=True,
                pool_pre_ping=True
            )
        return self._sql_engine

    @property
    def _get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """
        Get or create session factory.
        """
        if self._session_local is None:
            self._session_local = async_sessionmaker(
                autocommit=False,
                expire_on_commit=False,
                bind=self.sql_engine,
                class_=AsyncSession,
            )
        return self._session_local

    @asynccontextmanager
    async def get_sql_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager for sql sessions.

        Usage:
            async with db_manager.get_sql_session() as session:
                result = await session.execute(query)
        """
        session_factory = self._get_session_factory
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    # ==================== Neo4j ====================
    @property
    def neo4j_driver(self) -> AsyncDriver:
        """
        Lazy initialization of Neo4j driver.
        """
        if self._neo4j_driver is None:
            self._neo4j_driver = AsyncGraphDatabase.driver(
                self.settings.NEO4J_URI,
                auth=(self.settings.NEO4J_USER, self.settings.NEO4J_PASSWORD),
            )
        return self._neo4j_driver

    @asynccontextmanager
    async def get_neo4j_session(
            self, database: str = "neo4j"
    ) -> AsyncGenerator[Neo4jAsyncSession, None]:
        """
        Context manager for Neo4j sessions.
        Usage:
            async with db_manager.get_neo4j_session() as session:
                result = await session.run("MATCH (n) RETURN n LIMIT 10")
        """
        async with self.neo4j_driver.session(database=database) as session:
            try:
                yield session
            except Exception:
                raise

    async def execute_neo4j_query(
            self,
            query: str,
            parameters: dict = None,
            database: str = "neo4j"
    ):
        """
        Execute Neo4j query and return results.
        Arguments:
            query: Cypher query string.
            parameters: Optional parameters to pass to Neo4j.
            database: Neo4j database name.
        Returns:
            List of results.
        """
        async with self.neo4j_driver.session(database=database) as session:
            result = await session.run(query, parameters or {})
            return result.data()

    # ==================== Redis ====================
    @property
    def redis_client(self) -> Redis:
        """
        Lazy initialization of Redis client.
        """
        if self._redis_client is None:
            self._redis_client = aioredis.from_url(
                self.settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return self._redis_client

    async def get_redis_value(self, key: str) -> Optional[str]:
        """
        Get value from Redis.
        """
        return await self.redis_client.get(key)

    async def set_redis_value(
            self, key: str, value: str, expire: Optional[int] = None
    ) -> bool:
        """
        Set value in Redis.

        Arguments:
            key: Redis key.
            value: Value to store
            expire: Expiration time in seconds.

        Returns:
            True on success.
        """
        return await self.redis_client.set(key, value, ex=expire)

    async def delete_redis_key(self, key: str) -> int:
        """
        Delete key from Redis.
        """
        return await self.redis_client.delete(key)

    # ==================== Initialization & Health Checks ====================
    async def _check_sql(self):
        try:
            async with self.sql_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                return True, None
        except Exception as e:
            return False, f"❌ SQL database connection failed: {e}"

    async def _check_neo4j(self):
        try:
            await self.neo4j_driver.verify_connectivity()
            return True, None
        except Exception as e:
            return False, f"❌ Neo4j connection failed: {e}"

    async def _check_redis(self):
        try:
            await self.redis_client.ping()
            return True, None
        except Exception as e:
            return False, f"❌ Redis connection failed: {e}"

    async def initialize(self):
        """
        Initialize all database connections and verify connectivity.
        """
        checks = {
            "SQL": self._check_sql,
            "Neo4j": self._check_neo4j,
            "Redis": self._check_redis,
        }
        results = await asyncio.gather(*(check() for check in checks.values()))
        errors = []
        for (is_ok, error_msg), name in zip(results, checks.keys()):
            if is_ok:
                print(f"✅ {name} connected successfully")
            else:
                errors.append(error_msg)
        if errors:
            raise RuntimeError(
                f"Database initialization failed:\n" + "\n".join(errors)
            )

    async def health_check(self) -> dict:
        sql_status, neo4j_status, redis_status = await asyncio.gather(
            self._check_sql(),
            self._check_neo4j(),
            self._check_redis(),
        )
        return {
            "sql": sql_status[0],
            "neo4j": neo4j_status[0],
            "redis": redis_status[0],
        }

    # ==================== Table Management ====================
    async def create_all_tables(self, base: Base):
        """create all tables."""
        async with self.sql_engine.begin() as conn:
            await conn.run_sync(base.metadata.create_all)
        print(f"✅ All SQL tables created.")

    async def drop_all_tables(self, base: Base):
        """drop all tables."""
        async with self.sql_engine.begin() as conn:
            await conn.run_sync(base.metadata.drop_all)
        print(f"✅ All SQL tables Dropped.")

    async def create_neo4j_constraints(self):
        """
        Create Neo4j constraints and indexes.
        You should customize this based on your schema.
        """
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
            "CREATE INDEX IF NOT EXISTS FOR (u:User) ON (u.email)",
            # Add more constraints as needed
        ]

        async with self.get_neo4j_session() as session:
            for constraint in constraints:
                try:
                    await session.run(constraint)
                except Exception as e:
                    print(f"Warning: Failed to create constraint: {e}")
        print("✓ Neo4j constraints created")

    async def clear_neo4j_database(self):
        """Clear all nodes and relationships in Neo4j. Use with caution!"""
        async with self.get_neo4j_session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
        print("✓ Neo4j database cleared")

    # ==================== Cleanup ====================
    async def close(self):
        """Close all database connections gracefully."""
        errors = []

        # Close SQL engine
        if self._sql_engine:
            try:
                await self._sql_engine.dispose()
                print("✅ SQL engine closed")
            except Exception as e:
                errors.append(f"SQL close error: {e}")

        # Close Neo4j driver
        if self._neo4j_driver:
            try:
                await self._neo4j_driver.close()
                print("✅Neo4j driver closed")
            except Exception as e:
                errors.append(f"Neo4j close error: {e}")

        # Close Redis client
        if self._redis_client:
            try:
                await self._redis_client.close()
                print("✅Redis client closed")
            except Exception as e:
                errors.append(f"Redis close error: {e}")

        if errors:
            print("Warnings during cleanup:\n" + "\n".join(errors))


db_manager = DatabaseManager(settings)
