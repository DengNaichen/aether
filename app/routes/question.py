import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from redis.asyncio import Redis
from neomodel import db, DoesNotExist

from app.models.user import User
from app.schemas.questions import AnyQuestion, QuestionType, QuestionDifficulty
from app.core.deps import get_redis_client
from app.core.deps import get_current_admin_user
from app.routes.utils import queue_bulk_import_task
from app.worker.config import WorkerContext
from app.core.deps import get_worker_context
import app.models.neo4j_model as neo

router = APIRouter(
    prefix="/questions",
    tags=["Question"]
)


class QuestionAlreadyExistsError(Exception):
    pass


def pydantic_to_neomodel(question: AnyQuestion) -> neo.Question:
    """
    Convert the Pydantic model to an unsaved NeoModel model
    """
    common_data = {
        "question_id": question.question_id,
        "question_type": question.question_type,
        "difficulty": question.difficulty.value,
        "knowledge_node_id": question.knowledge_node_id,
        "text": question.text,
        "details": question.details,
    }

    if question.question_type == QuestionType.FILL_IN_THE_BLANK:
        return neo.FillInBlank(
            **common_data,
            expected_answer=question.details.expected_answer
        )
    elif question.question_type == QuestionType.MULTIPLE_CHOICE:
        return neo.MultipleChoice(
            **common_data,
            options=question.details.options,
            correct_answer=question.details.correct_answer
        )
    elif question.question_type == QuestionType.CALCULATION:
        return neo.Calculation(
            **common_data,
            expected_answer=question.details.expected_answer,
            precision=question.details.precision
        )
    else:
        raise ValueError(f"Unknown question type: {question.question_type}")


def _create_question_sync(
        question_data: AnyQuestion,
):
    q_id = str(question_data.question_id)
    # TODO: this two line need to be reconsider
    # existing_question = neo.Question.nodes.get_or_none(question_id=q_id)
    #
    # if existing_question:
    #     raise QuestionAlreadyExistsError(f"Question {q_id} already exists")

    kn_id_to_find = str(question_data.knowledge_node_id)
    try:
        knowledge_node_to_connect = neo.KnowledgeNode.nodes.get(
            node_id=kn_id_to_find
        )
    except DoesNotExist:
        raise ValueError(
            f"Knowledge node {kn_id_to_find} does not exist"
            "Cannot create question because of the knowledge node"
        )
    except Exception as e:
        raise Exception(f"Error fetching knowledge node {kn_id_to_find}: {e}")

    new_question = pydantic_to_neomodel(question_data)

    new_question.save()
    new_question.knowledge_node.connect(knowledge_node_to_connect)
    new_question.save()

    # return new_question


@router.post("/",
             status_code=status.HTTP_201_CREATED,
             summary="create a new question",
             response_model=AnyQuestion,
             )
async def create_question(
        question_data: AnyQuestion,
        ctx: WorkerContext = Depends(get_worker_context),
        admin: User = Depends(get_current_admin_user),
) -> AnyQuestion:
    try:
        async with (ctx.neo4j_scoped_connection()):
            await asyncio.to_thread(
                _create_question_sync,
                question_data
            )
        return question_data

    except QuestionAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except TypeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create new question: {e}"
        )


@router.post(
    "/bulk",
    status_code=status.HTTP_202_ACCEPTED,
    summary="queue a task to bulk create questions from csv",
)
async def bulk_queue_questions(
        question_file: UploadFile = File(...),
        redis_client: Redis = Depends(get_redis_client),
        admin: User = Depends(get_current_admin_user)
):
    file_path, _ = await queue_bulk_import_task(
        file=question_file,
        redis_client=redis_client,
        task_type="handle_bulk_import_question",
        extra_payload={"requested_by": admin.email}
    )
    return {
        "message": "Bulk questions creation queued",
        "file_path": str(file_path)
    }






