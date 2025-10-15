import asyncio
import json
import traceback
from typing import Callable, Dict

from datetime import datetime, timezone

from src.app.core.database import db_manager, DatabaseManager
from contextlib import asynccontextmanager

MAX_RETRIES = 3
RETRY_DELAY_BASE = 2  # in seconds
MAIN_QUEUE_NAME = "general_task_queue"
DLQ_NAME = "general_task_dlq"  # The name for our Dead-Letter Queue


class WorkerContext:
    def __init__(self, db_mng: DatabaseManager):
        self.db_manager = db_mng

    @property
    def neo4j_driver(self):
        return self.db_manager.neo4j_driver

    @property
    def redis_driver(self):
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


TASK_HANDLERS: Dict[str, Callable] = {}


def register_handler(task_type: str):
    def decorator(func):
        TASK_HANDLERS[task_type] = func
        return func
    return decorator


@register_handler("handle_neo4j_create_course")
async def handle_neo4j_create_course(payload: dict, ctx: WorkerContext):
    course_id = payload.get("course_id")
    course_name = payload.get("course_name")

    if not course_id:
        raise ValueError(f"Missing course id: {course_id} for graph database sync")

    async with ctx.neo4j_driver.session() as session:
        await session.run(
            "MERGE (c: Course {id: $id, name: $name})",
            id=course_id,
            name=course_name,
        )
    print(f"✅ Course {course_id} synced to graph database")


async def move_to_dlq(
        redis_client,
        task: dict,
        error_message: str,
        retry_count: int = 0
):
    dlq_payload = {
        "original_task": task,
        "error_message": error_message,
        "retry_count": retry_count,
        "failed_at": datetime.now(timezone.utc).isoformat(),
        "traceback": traceback.format_exc(),
    }

    await redis_client.lpush(DLQ_NAME, json.dumps(dlq_payload))
    task_type = task.get("task_type", "unknown")
    print(f"🚨 Task move to DLQ: {task.get("task_type")}")


async def process_task(task_data: str, ctx: WorkerContext, max_retries: int = 3):
    task = json.loads(task_data)
    task_type = task.get("task_type")
    payload = task.get("payload", {})

    handler = TASK_HANDLERS.get(task_type)
    if not handler:
        print(f"⚠️ Unknow task type: {task_type}. Move to DLQ")
        await move_to_dlq(ctx.redis_client, task, "Unknow task type")
        return

    for attempt in range(MAX_RETRIES):
        try:
            await handler(payload, ctx)
            print(f"✅ Successfully processed task of type: {task_type}")
            return
        except Exception as e:
            print(f"❌ Attempt #{attempt + 1}/{max_retries} failed for task '{task_type}': {e}")
            if attempt + 1 == max_retries:
                await move_to_dlq(ctx.redis_client, task, str(e))

            else:
                await asyncio.sleep(2 ** attempt)


class WorkerStats:

    def __init__(self):
        self.processed_count = 0
        self.failed_count = 0
        self.start_time = datetime.now(timezone.utc)

    def increment_processed(self):
        self.processed_count += 1

    def increment_failed(self):
        self.failed_count += 1

    def get_stats(self) -> dict:
        runtime = (datetime.now() - self.start_time).total_seconds()
        return {
            "processed_count": self.processed_count,
            "failed_count": self.failed_count,
            "runtime": runtime,
            "throughput": self.processed_count / runtime if runtime > 0 else 0,
            "start_time": self.start_time.isoformat(),
        }

    def print_stats(self):
        stats = self.get_stats()
        print(f"\n{'=' * 50}")
        print(f"📊 Worker Statistics")
        print(f"{'=' * 50}")
        print(f"✅ Processed: {stats['processed']}")
        print(f"❌ Failed: {stats['failed']}")
        print(f"⏱️  Runtime: {stats['runtime_seconds']:.2f}s")
        print(f"🚀 Throughput: {stats['throughput']:.2f} tasks/sec")
        print(f"{'=' * 50}\n")


class AsyncWorker:

    def __init__(self, db_mng: DatabaseManager, queue_name: str = MAIN_QUEUE_NAME):
        self.db_manager = db_mng
        self.queue_name = queue_name
        self.ctx = WorkerContext(db_mng)
        self.stats = WorkerStats()
        self.running = False

    async def start(self):
        """Start the worker."""
        print(f"\n{'='*50}")
        print(f"🚀 Starting Worker")
        print(f"{'=' * 50}")
        print(f"📥 Listening on queue: {self.queue_name}")
        print(f"📊 DLQ: {DLQ_NAME}")
        print(f"🔄 Max retries: {MAX_RETRIES}")
        print(f"📝 Registered handlers: {len(TASK_HANDLERS)}")
        for task_type in TASK_HANDLERS.keys():
            print(f"   - {task_type}")
        print(f"{'=' * 50}\n")

        await self.db_manager.initialize()

        self.running = True

        try:
            await self._run_loop()
        except KeyboardInterrupt:
            print("\n⚠️ Received shutdown signal...")
        finally:
            await self.shutdown()

    async def _run_loop(self):
        """
        main loop
        """
        while self.running:
            try:
                result = await self.ctx.redis_client.brpop(
                    self.queue_name,
                    timeout=1
                )

                if result is None:
                    continue

                _, task_data = result

                try:
                    await process_task(task_data, self.ctx)
                    self.stats.increment_processed()
                except Exception as e:
                    print(f"🚨 Critical error processing task: {e}")
                    self.stats.increment_failed()

                if self.stats.processed_count % 100 == 0:
                    self.stats.print_stats()

            except Exception as e:
                print(f"🚨 Worker loop error: {e}")
                await asyncio.sleep(1)

    async def shutdown(self):
        """
        showdown the worker
        """
        print("\n Shutting down worker")
        self.running = False
        self.stats.print_stats()
        await db_manager.close()
        print("✅ Worker shutdown complete\n")


async def main():
    worker = AsyncWorker(db_manager, MAIN_QUEUE_NAME)
    await worker.start()
