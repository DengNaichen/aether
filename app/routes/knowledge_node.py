import json

from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.deps import get_db, get_redis_client
from app.models.knowledge_node import KnowledgeNode
from app.helper.course_helper import assemble_course_id
from app.schemas.knowledge_node import KnowledgeNodeRequest

router = APIRouter(
    prefix="/knowledge",
    tags=["knowledge"],
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new knowledge node",
    response_model=KnowledgeNode,
)
async def create_knowledge_node(
        knowledge_node: KnowledgeNodeRequest,
        db: AsyncSession = Depends(get_db),
        redis_client: Redis = Depends(get_redis_client)
) -> KnowledgeNode:
    course_id = assemble_course_id(knowledge_node.course_id)

    await check_repeat_knowledge_node(knowledge_node.id, db)

    new_knowledge_node = KnowledgeNode(
        id=knowledge_node.id,
        name=knowledge_node.name,
        course_id=course_id,
        description=knowledge_node.description
    )
    db.add(new_knowledge_node)

    try:
        await db.commit()
        await db.refresh(new_knowledge_node)

        task = {
            "task_type": "handle_neo4j_create_knowledge_node",
            "payload": {
                "knowledge_node_id": new_knowledge_node.id,
                "course_id": course_id,
                "name": new_knowledge_node.name,
                "description": knowledge_node.description
            }
        }

        await redis_client.publish("general_task_queue", json.dumps(task))

        print(f"📤 Task queued for knowledge node id {new_knowledge_node.id}")
        return new_knowledge_node

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create knowledge node {new_knowledge_node.id}"
        )


async def check_repeat_knowledge_node(knowledge_node_id: str, db: AsyncSession):
    from sqlalchemy import select
    stmt = select(KnowledgeNode).where(KnowledgeNode.id == knowledge_node_id)
    result = await db.execute(stmt)
    existing_knowledge_node = result.scalar_one_or_none()

    if existing_knowledge_node is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Knowledge node id {knowledge_node_id} already exist"
        )
