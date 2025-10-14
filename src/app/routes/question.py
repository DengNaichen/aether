from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from src.app.core.deps import get_neo4j_driver
from src.app.schemas.questions import AnyQuestion

router = APIRouter(prefix="/question", tags=["Question"])


@router.post("/", summary="create a new question(Neo4j)")
async def create_question(
    question_data: AnyQuestion, neo4j_driver=Depends(get_neo4j_driver)
):
    # Convert Pydantic model to Neo4j node
    node_properties = {
        "id": str(question_data.id),
        "text": question_data.text,
        "difficulty": question_data.difficulty.value,
        "created_at": datetime.now(timezone.utc),
    }
    node_properties.update(question_data.details.model_dump())

    if question_data.question_type == "multiple_choice":
        labels = ":Question:MultipleChoice"
    elif question_data.question_type == "fill_in_the_blank":
        labels = ":Question:FillInTheBlank"
    else:
        raise HTTPException(status_code=400, detail="Unsupported question type")

    query = f"""
    MATCH (kp:KnowledgePoint {{id: $kpid}})
    CREATE (q{labels} $props)
    CREATE (q)-[:TESTS]->(kp)
    RETURN q.id AS create_id
    """

    async with await neo4j_driver.session() as session:
        result = await session.run(
            query, kpid=question_data.knowledge_point_id, props=node_properties
        )
        record = await result.single()
        if not record:
            raise HTTPException(
                status_code=500, detail="Failed to create question or link it"
            )

    return {"status": "success", "data": question_data}
