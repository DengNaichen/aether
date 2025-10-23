import asyncio

import pytest
from httpx import AsyncClient
from fastapi import status


from app.core.database import DatabaseManager
import app.schemas.questions as pydantic
import app.models.neo4j_model as neo


@pytest.mark.asyncio
async def test_create_question_successful(
        authenticated_admin_client: AsyncClient,
        nodes_in_neo4j_db,
        test_db_manager: DatabaseManager,
):
    client = authenticated_admin_client
    target_node, source_node = nodes_in_neo4j_db

    target_node_id = target_node.node_id

    pydantic_question = pydantic.MultipleChoiceQuestion(
        difficulty=pydantic.QuestionDifficulty.EASY,
        text="what is the capital of France?",
        knowledge_node_id=target_node_id,
        details=pydantic.MultipleChoiceDetails(
            options=["London", "Paris", "Berlin", "Madrid"],
            correct_answer=1
        )
    )
    json_request = pydantic_question.model_dump(mode='json')

    url = "/questions/"
    response = await client.post(url, json=json_request)

    assert response.status_code == 201

    async with test_db_manager.neo4j_scoped_connection():
        db_target_node = neo.KnowledgeNode.nodes.get(
            node_id=target_node.node_id
        )
        db_question_node = neo.MultipleChoice.nodes.get(
            question_id=pydantic_question.question_id
        )

        assert db_target_node is not None
        assert db_question_node is not None

        connected_kn = db_question_node.knowledge_node.get()
        assert connected_kn is not None, ("Question is not connected "
                                          "to any KnowledgeNode")

        assert connected_kn.element_id == db_target_node.element_id
