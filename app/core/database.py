import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from redis.asyncio import Redis
import redis.asyncio as aioredis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, settings
from app.models.base import Base


class DatabaseManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._sql_engine: Optional[AsyncEngine] = None
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
                # echo=self.settings.is_testing,
                echo=False,
                future=True,
                pool_pre_ping=True,
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

    # ==================== Redis ====================
    @property
    def redis_client(self) -> Redis:
        """
        Lazy initialization of Redis client.
        """
        if self._redis_client is None:
            self._redis_client = aioredis.from_url(
                self.settings.REDIS_URL, encoding="utf-8", decode_responses=True
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
            # "Neo4j": self._check_neo4j,
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
            raise RuntimeError(f"Database initialization failed:\n" + "\n".join(errors))

    async def health_check(self) -> dict:
        sql_status, redis_status = await asyncio.gather(
            self._check_sql(),
            self._check_redis(),
        )
        return {
            "sql": sql_status[0],
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
