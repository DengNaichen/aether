from typing import Callable, Dict

from contextlib import asynccontextmanager

from app.core.database import DatabaseManager


MAX_RETRIES = 3
RETRY_DELAY_BASE = 2  # in seconds
MAIN_QUEUE_NAME = "general_task_queue"
DLQ_NAME = "general_task_dlq"  # The name for our Dead-Letter Queue
TASK_HANDLERS: Dict[str, Callable] = {}


class WorkerContext:
    def __init__(self, db_mng: DatabaseManager):
        self.db_manager = db_mng

    @property
    def neo4j_driver(self):
        return self.db_manager.neo4j_driver

    @property
    def redis_client(self):
        return self.db_manager.redis_client

    @asynccontextmanager
    async def neo4j_session(self):
        """
        get Neo4J session
        """
        async with self.db_manager.get_neo4j_session() as session:
            yield session

    @asynccontextmanager
    async def sql_session(self):
        async with self.db_manager.get_sql_session() as session:
            yield session

    @asynccontextmanager
    async def neo4j_scoped_connection(self):
        async with self.db_manager.neo4j_scoped_connection():
            yield


def register_handler(task_type: str):
    def decorator(func):
        TASK_HANDLERS[task_type] = func
        return func
    return decorator
