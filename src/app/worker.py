import asyncio
import json
import traceback

import redis
from datetime import datetime, timezone
from neo4j import AsyncGraphDatabase

# --- Configuration ---
# In a real app, load these from environment variables!
REDIS_HOST = "localhost"
REDIS_PORT = 6379
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "your_neo4j_password" # TODO: Change this!

MAX_RETRIES = 3
RETRY_DELAY_BASE = 2  # in seconds
MAIN_QUEUE_NAME = "general_task_queue"
DLQ_NAME = "general_task_dlq"  # The name for our Dead-Letter Queue


class WorkerContext:
    def __init__(self, neo4j_driver, redis_client):
        self.neo4j_driver = neo4j_driver
        self.redis_client = redis_client


TASK_HANDLERS = {}


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


async def move_to_dlq(redis_client, task: dict, error_message: str):
    dlq_payload = {
        "original_task": task,
        "error_message": error_message,
        "failed_at": datetime.now(timezone.utc).isoformat(),
        "traceback": traceback.format_exc(),
    }
    await redis_client.lpush(DLQ_NAME, json.dumps(dlq_payload))
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


asynccon





async def main():
    """The main worker process"""
    neo4j_driver = AsyncGraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD),
    )
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    sync_redis_client = redis.asyncio.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}", decode_responses=True)

    print("✅ Worker is running and waiting for tasks...")

    while True:
        task_message = None
        try:
            # BRPOP blocks the connection until a task is avaliable in the queue
            #
            _queue, task_message_str = redis_client.brpop(MAIN_QUEUE_NAME)


            print(f"📩 Received task of type: {task_type}")




            succeeded = False


        except Exception as e:
            print(f"🚨 A critical error occurred: {e}")
            if task_message_str:
                await move_to_dlq(redis_client, {"raw_message": task_message_str}, str(e))



