import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.models.user import User
from app.models.question import Question
from app.schemas.questions import AnyQuestion
from app.core.deps import get_db, get_redis_client
from app.core.deps import get_current_admin_user

router = APIRouter(
    prefix="/question",
    tags=["question"]
)


@router.post("/",
             status_code=status.HTTP_201_CREATED,
             summary="create a new question",
             response_model=AnyQuestion,
             )
async def create_question(
        question_data: AnyQuestion,
        db: AsyncSession = Depends(get_db),
        redis_client: Redis = Depends(get_redis_client),
        admin: User = Depends(get_current_admin_user)
):
    new_questions = Question(
        id=question_data.id,
        text=question_data.text,
        # TODO: should I convert them to string for the sql ?
        difficulty=question_data.difficulty,
        question_type=question_data.question_type,
        details=question_data.details.model_dump(),
        knowledge_node_id=question_data.knowledge_point_id
    )
    db.add(new_questions)

    try:
        await db.commit()
        await db.refresh(new_questions)

        task = {
            "task_type": "handle_neo4j_create_question",
            "payload": {
                "question_id": new_questions.id,
                "question_type": new_questions.question_type.value,
                "difficulty": new_questions.difficulty.value,
                "knowledge_node_id": new_questions.knowledge_node_id
            }
        }

        await redis_client.publish("general_task_queue", json.dumps(task))

        print(f"📤 Task queued for knowledge node id {new_questions.id}")
        return new_questions

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create new question: {e}"
        )





