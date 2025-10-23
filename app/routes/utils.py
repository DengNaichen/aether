import aiofiles
import aiofiles.os
import uuid
import json
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from redis.asyncio import Redis

UPLOAD_DIR = Path("./temp_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def queue_bulk_import_task(
        file: UploadFile,
        redis_client: Redis,
        task_type: str,
        queue_name: str = "general_task_queue",
        extra_payload: dict | None = None
) -> tuple[Path, dict]:
    
    # --- 1. Save the uploaded file temporarily ----
    if file.content_type != "text/csv":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be of type text/csv",
        )

    temp_filename = f"bulk_import_{uuid.uuid4()}.csv"
    file_path = UPLOAD_DIR / temp_filename  # TODO: here has some problems

    try:
        async with aiofiles.open(file_path, 'wb') as out_files:
            while content := await file.read(1024 * 1024):
                await out_files.write(content)
    
    except Exception as e:
        # Clean up if saving fails
        if await aiofiles.os.path.exists(file_path):
            await aiofiles.os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {e}"
        )
    
    finally:
        await file.close()

    
    # --- 2. Queue the task for the worker ----
    try:
        task_payload = {"file_path": str(file_path)}
        if extra_payload:
            task_payload.update(extra_payload)

        task = {
            "task_type": task_type,
            "payload": task_payload
        }
    
        await redis_client.lpush("general_task_queue", json.dumps(task))

        return file_path, task_payload
    
    except Exception as e:
        if await aiofiles.os.path.exists(file_path):
            await aiofiles.os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue bulk import task: {e}"
        )