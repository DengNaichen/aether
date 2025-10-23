from fastapi import APIRouter, HTTPException, status, UploadFile, File
from fastapi.params import Depends
from neomodel import DoesNotExist
from redis.asyncio import Redis

from app.core.deps import get_db, get_redis_client
from app.models.user import User
from app.helper.course_helper import assemble_course_id
from app.schemas.knowledge_node import KnowledgeNodeCreate, RelationType, \
    KnowledgeRelationCreate

from app.core.deps import get_current_admin_user, get_worker_context
from app.schemas.knowledge_node import KnowledgeNodeResponse
from app.worker.config import WorkerContext
import app.models.neo4j_model as neo
from app.routes.utils import queue_bulk_import_task


# TODO: the following part need to be changed to another file ?
class NodeAlreadyExistsError(Exception):
    pass


async def _create_knowledge_node_sync(
        course_id: str,
        node_data: KnowledgeNodeCreate,
) -> neo.KnowledgeNode:
    try:
        course = neo.Course.nodes.get(course_id=course_id)
    except DoesNotExist:
        raise ValueError(f"Course {course_id} does not exist")

    if neo.KnowledgeNode.nodes.first_or_none(node_id=node_data.id):
        raise NodeAlreadyExistsError(f'Node {node_data.node_id} already exists')

    new_node = neo.KnowledgeNode(
        node_id=node_data.id,
        node_name=node_data.name,
        description=node_data.description,
    ).save()
    new_node.course.connect(course)

    return new_node


async def _create_knowledge_relation_sync(
        relation: KnowledgeRelationCreate,
) -> dict:
    try:
        source_node = neo.KnowledgeNode.nodes.get(
            node_id=relation.source_node_id
        )
        target_node = neo.KnowledgeNode.nodes.get(
            node_id=relation.target_node_id
        )
    except DoesNotExist:
        raise ValueError(f"Source or Target node does not exist")

    if relation.relation_type == RelationType.HAS_PREREQUISITES:
        source_node.prerequisites.connect(target_node)
        # todo: how about another relations?
    elif relation.relation_type == RelationType.HAS_SUBTOPIC:
        source_node.subtopic.connect(target_node)
    elif relation.relation_type == RelationType.IS_EXAMPLE_OF:
        source_node.concept_this_is_example_of.connect(target_node)

    else:
        raise TypeError(f"Unknown relation type {relation.relation_type}")

    return {
        "status": "success",
        "source": source_node.node_id,
        "target": target_node.node_id,
        "relation": relation.relation_type.value,
    }


router = APIRouter()


@router.post(
    "/courses/{course_id}/node",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new knowledge node",
    response_model=KnowledgeNodeResponse,
)
async def create_knowledge_node(
        course_id: str,
        node: KnowledgeNodeCreate,
        ctx: WorkerContext = Depends(get_worker_context),
        admin: User = Depends(get_current_admin_user)
) -> KnowledgeNodeResponse:
    """ Create a new knowledge node under a course with course id

    """

    node_course_id = assemble_course_id(node.grade, node.subject)

    if course_id != node_course_id:
        raise HTTPException(
            status_code=400,
            detail="URL course_id does not match node's course details"
        )

    try:
        async with ctx.neo4j_scoped_connection():
            new_knowledge_node = await _create_knowledge_node_sync(course_id,
                                                                   node)

        responses = KnowledgeNodeResponse(
            id=node.id,
            name=node.name,
            course_id=node_course_id,
            description=node.description,
        )

        return responses

    except NodeAlreadyExistsError as e:
        raise HTTPException(
            status_code=409,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {e}"
        )


@router.post(
    "/courses/{course_id}/relationship",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new knowledge relation in the neo4j database",
)
async def create_knowledge_relation(
        relation: KnowledgeRelationCreate,
        ctx: WorkerContext = Depends(get_worker_context),
        admin: User = Depends(get_current_admin_user)
) -> dict:
    """ Create a new knowledge relation under a course

    Relationship Types:
        - HAS_PREREQUISITE: Source node requires target node as prerequisite
          (e.g., "Oxidation-Reduction" requires "Electron Transfer")
        - HAS_SUBTOPIC: Source node contains target node as a subtopic
          (e.g., "Acids and Bases" contains "pH Scale")
        - IS_EXAMPLE_OF: Source node is a concrete example of target node
          (e.g., "HCl" is an example of "Strong Acid")

    Args:
        relation: The relationship request containing:
            - source_node_id: ID of the source knowledge node
            - target_node_id: ID of the target knowledge node
            - relation_type: Type of relationship (enum value)

        ctx: WorkerContext for task queuing
        admin: Admin user
    """

    try:
        async with ctx.neo4j_scoped_connection():
            result = await _create_knowledge_relation_sync(relation)
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except TypeError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {e}"
        )


@router.post(
    "/courses/nodes/bulk",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue a task to bulk create new knowledge node from a csv file",
)
async def bulk_nodes(
        node_file: UploadFile = File(..., description="A CSV file of node"),
        redis_client: Redis = Depends(get_redis_client),
        admin: User = Depends(get_current_admin_user)
):
    file_path, _ = await queue_bulk_import_task(
        file=node_file,
        redis_client=redis_client,
        task_type="handle_bulk_import_nodes",
        extra_payload={"requested_by": admin.email}
    )
    return {"message": "Bulk node creation task queued.", 
            "file_path": str(file_path)}


@router.post(
    "/courses/relationships/bulk",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue a task to bulk create new knowledge relation from csv file",
)
async def bulk_relations(
        relation_file: UploadFile = File(...),
        redis_client: Redis = Depends(get_redis_client),
        admin: User = Depends(get_current_admin_user)
):
    file_path, _ = await queue_bulk_import_task(
        file=relation_file,
        redis_client=redis_client,
        task_type="handle_bulk_import_relations",
        extra_payload={"requested_by": admin.email}  # TODO: think about this
    )
    return {"message": "Bulk relation creation task queued.",
            "file_path": str(file_path)}
