import asyncio
import json
import traceback
from datetime import UTC, datetime

from app.core.database import DatabaseManager, db_manager
from app.worker.config import (
    DLQ_NAME,
    MAIN_QUEUE_NAME,
    MAX_RETRIES,
    TASK_HANDLERS,
    WorkerContext,
)


async def move_to_dlq(
    redis_client, task: dict, error_message: str, retry_count: int = 0
):
    dlq_payload = {
        "original_task": task,
        "error_message": error_message,
        "retry_count": retry_count,
        "failed_at": datetime.now(UTC).isoformat(),
        "traceback": traceback.format_exc(),
    }

    await redis_client.lpush(DLQ_NAME, json.dumps(dlq_payload))
    # task_type = task.get("task_type", "unknown")
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
            print(
                f"❌ Attempt #{attempt + 1}/{max_retries} failed for task '{task_type}': {e}"
            )
            if attempt + 1 == max_retries:
                await move_to_dlq(ctx.redis_client, task, str(e))

            else:
                await asyncio.sleep(2**attempt)


class WorkerStats:

    def __init__(self):
        self.processed_count = 0
        self.failed_count = 0
        self.start_time = datetime.now(UTC)

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
        print("📊 Worker Statistics")
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
        print("🚀 Starting Worker")
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
                result = await self.ctx.redis_client.brpop(self.queue_name, timeout=1)

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
    """Main entry point for the worker."""
    worker = AsyncWorker(db_manager)
    await worker.start()


# Auto-start the worker when this module is run
if __name__ == "__main__":
    asyncio.run(main())
else:
    # When run as a module (python -m app.worker.worker), also start
    import sys

    if "app.worker.worker" in sys.modules:
        # Check if we're being run as the main module
        if sys.argv[0].endswith("worker.py") or sys.argv[0].endswith("-m"):
            asyncio.run(main())
