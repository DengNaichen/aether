import uuid
from http.client import responses
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from httpx import AsyncClient

from src.app.core.deps import get_neo4j_driver
from src.app.main import app

mock_neo4j_driver, mock_neo4j_session = AsyncMock(), AsyncMock()
mock_neo4j_driver.session.return_value.__aenter__.return_value = mock_neo4j_session


async def override_get_neo4j_driver():
    return mock_neo4j_driver


app.dependency_overrides[get_neo4j_driver] = override_get_neo4j_driver


@pytest.mark.asyncio
async def test_create_multiple_choice_question_success():
    mock_record = MagicMock()
    mock_record.get.return_value = str(uuid.uuid4())

    # configure the mock session's run method to return
    mock_neo4j_session.run.return_value.single.return_value = mock_record

    # Create the json payload
    test_question_id = str(uuid.uuid4())
    question_payload = {
        "id": test_question_id,
        "text": "what is the speed of light?",
        "difficulty": "easy",
        "knowledge_point_id": "physics",
        "question_type": "multiple_choice",
        "details": {
            "options": [
                "299,792 km/s",
                "150,000 km/s",
                "1,080 million km/h",
                "300,000 km/s",
            ],
            "correct_answer": 0,
        },
    }
    async with AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/question/", json=question_payload)

    assert response.status_code == 200
    response_data = response.json()
    # check response data structure
    assert response_data["status"] == "success"
    assert response_data["data"]["id"] == test_question_id
    assert response_data["data"]["difficulty"] == "easy"

    mock_neo4j_session.run.assert_called_once()


# @pytest.mark.asyncio
# async def test_get_question_by_id_success():
#     test_question_id = str(uuid.uuid4())
#     mock_question_data = {
#         "id": test_question_id,
#         "text": "what is the speed of light?",
#         "difficulty": "easy",
#         "knowledge_point_id": "physics",
#         "question_type": "multiple_choice",
#         "details": {
#             "options": [
#                 "299,792 km/s",
#                 "150,000 km/s",
#                 "1,080 million km/h",
#                 "300,000 km/s"
#             ],
#             "correct_answer": 0
#         }
#     }
#     mock_record = MagicMock()
#     mock_record.data.return_value = {"n": mock_question_data}
#
#     mock_neo4j_session.run.return_value.single.return_value = mock_record
#
#     async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test" ) as client:
#         response = await client.get(f"/question/{test_question_id}")
#
#     assert response.status_code == 200
#     response_data = response.json()
#     assert response_data["data"]["id"] == test_question_id
#     assert response_data["data"]["text"] == "what is the speed of light?"
#
#     mock_neo4j_session.run.assert_called_once()
