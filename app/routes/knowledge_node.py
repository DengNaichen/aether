import csv
import json
from idlelib.iomenu import errors

from fastapi import APIRouter, HTTPException, status, UploadFile, File
from fastapi.params import Depends
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from redis.asyncio import Redis

from app.core.deps import get_db, get_redis_client
from app.models.user import User
from app.models.knowledge_node import KnowledgeNode
from app.helper.course_helper import assemble_course_id
from app.schemas.knowledge_node import KnowledgeNodeCreate, RelationType, \
    KnowledgeRelationCreate

from app.crud.crud import check_knowledge_node, check_course_exist
from core.deps import get_current_admin_user

router = APIRouter(
    prefix="/courses",
    tags=["courses"],
)


@router.post(
    "{course_id}/node",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new knowledge node",
    response_model=KnowledgeNode,
)
async def create_knowledge_node(
        course_id: str,
        node: KnowledgeNodeCreate,
        db: AsyncSession = Depends(get_db),
        redis_client: Redis = Depends(get_redis_client),
        admin: User = Depends(get_current_admin_user)
) -> KnowledgeNode:
    """ Create a new knowledge node under a course with course id

    This endpoint create a knowledge node in the sql database and publishes
    a task to Redis for Neo4j graph creation. The course_id assembled from the
    grade and subject in the request body.

    Arg:
        course_id: The course id of the course
        node: The knowledge creation requestion constrain:
            - id(str): Unique identifier of the knowledge node
            - name(str): Name of the knowledge node
            - description (str): Description of the knowledge node
            - subject (Subject): Subject of the knowledge node
            - grade (Grade): Grade of the knowledge node
        db: Database session dependency
        redis_client: Redis session dependency, for task queuing
        admin: Admin user

    Returns:
         KnowledgeNode: The newly created knowledge node with all field populated

    Raises:
        HTTPException: 409 if the knowledge node already exists
        HTTPException: 500 if the internal server error occurred
    """
    node_course_id = assemble_course_id(node.grade, node.subject)

    assert course_id == node_course_id

    if_course_exist = await check_course_exist(course_id, db)
    if not if_course_exist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course does not exist"
        )

    if_node_exist = await check_knowledge_node(node.id, db)
    if if_node_exist:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Knowledge node already exists"
        )

    new_knowledge_node = KnowledgeNode(
        id=node.id,
        name=node.name,
        course_id=course_id,
        description=node.description
    )
    db.add(new_knowledge_node)

    try:
        await db.commit()
        await db.refresh(new_knowledge_node)

        task = {
            "task_type": "handle_neo4j_create_knowledge_node",
            "payload": {
                "node_id": new_knowledge_node.id,
                "course_id": course_id,
            }
        }

        await redis_client.publish("general_task_queue", json.dumps(task))

        print(f"📤 Task queued for knowledge node id {new_knowledge_node.id}")
        return new_knowledge_node

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create knowledge {new_knowledge_node.id}: {e}"
        )


@router.post(
    "/{course_id}/relationship",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new knowledge relation in the neo4j database",
)
async def create_knowledge_relation(
        course_id: str,
        relation: KnowledgeRelationCreate,
        db: AsyncSession = Depends(get_db),
        redis_client: Redis = Depends(get_redis_client),
        admin: User = Depends(get_current_admin_user)
):
    """ Create a new knowledge relation under a course

    This endpoint validates that both nodes exist in SQL, then queues an
    asynchronous task to create the relationship in the Neo4j graph database.
    The relationship itself is only stored in Neo4j for efficient graph
     traversal.

    Relationship Types:
        - HAS_PREREQUISITE: Source node requires target node as prerequisite
          (e.g., "Oxidation-Reduction" requires "Electron Transfer")
        - HAS_SUBTOPIC: Source node contains target node as a subtopic
          (e.g., "Acids and Bases" contains "pH Scale")
        - IS_EXAMPLE_OF: Source node is a concrete example of target node
          (e.g., "HCl" is an example of "Strong Acid")

    Args:
        course_id: The ID of the course containing both knowledge nodes
        relation: The relationship request containing:
            - source_node_id: ID of the source knowledge node
            - target_node_id: ID of the target knowledge node
            - relation_type: Type of relationship (enum value)
        db: Database session dependency for validation
        redis_client: Redis client dependency for task queuing
        admin: Admin user

    Returns:
        dict: Success message confirming the task was queued

    Raises:
        HTTPException: 400 if course doesn't exist
        HTTPException: 400 if source node doesn't exist
        HTTPException: 400 if target node doesn't exist
        HTTPException: 500 if Redis task queuing fails

    Note:
        - Both nodes must exist in SQL before creating the relationship
        - The actual Neo4j relationship creation is handled asynchronously
        - Relationships are not stored in SQL, only in Neo4j
        - Source data is maintained in CSV files for rebuild capability
    """
    if_course_exist = await check_course_exist(course_id, db)
    if not if_course_exist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course does not exist"
        )
    target_node_id = relation.target_node_id
    source_node_id = relation.source_node_id
    relation_type = relation.relation_type

    # check if the targe node and source node exist
    if_targe_exist = await check_knowledge_node(target_node_id, db)
    if_source_exist = await check_knowledge_node(source_node_id, db)
    if not if_source_exist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source node does not exist",
        )
    if not if_targe_exist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target node does not exist",
        )

    try:
        task = {
            "task_type": "handle_neo4j_create_knowledge_relation",
            "payload": {
                "course_id": course_id,
                "source_node_id": source_node_id,
                "target_node_id": target_node_id,
                "relation_type": relation_type,
            }
        }
        await redis_client.publish("general_task_queue", json.dumps(task))
        print(
            f"📤 Task queued for building relation relation between"
            f" {source_node_id} and {target_node_id} with relation type"
            f" {relation_type.value}")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create knowledge relation "
                   f"{relation_type.value}: {e}"
        )


@router.post(
    "/nodes/bulk",
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create new knowledge node from a csv file",
)
async def bulk_nodes(
        node_file: UploadFile = File(..., description="A CSV file of node"),
        db: AsyncSession = Depends(get_db),
):
    if node_file.content_type != "text/csv":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be of type text/csv",
        )
    nodes_to_create = []
    error = []
    try:
        contents = await node_file.read()
        decoded_contents = contents.decode("utf-8")
        csv_reader = csv.DictReader(decoded_contents)

        for i, row in enumerate(csv_reader):
            row_num = i + 2
            try:
                node_data = KnowledgeNodeCreate.parse_obj(row)
                db_node = KnowledgeNode(**node_data.dict())
                nodes_to_create.append(db_node)
            except ValidationError as e:
                error.append({"row": row_num, "message": str(e)})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read or parse csv file: {e}")

    if not nodes_to_create:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "No nodes to create.", "errors": errors}
        )

    # TODO: finish the design of this function
    try:
        db.add_all(nodes_to_create)
        await db.commit()
    except Exception as e:
        await db.rollback()



@router.post(
    "/relationships/bulk",
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create new knowledge relation from a csv file",
)
async def bulk_relations(
        rlt_file: UploadFile = File(..., description="A CSV file of node"),
        db: AsyncSession = Depends(get_db),
):
    if rlt_file.content_type != "text/csv":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be of type text/csv",
        )
    nodes_to_create = []
    error = []
    # TODO: finish the design of this function
