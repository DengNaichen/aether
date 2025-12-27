# from typing import Any

# import app.models.neo4j_model as neo
# import pytest
# from app.routes.quiz import (
#     get_random_question_for_user,
#     get_validated_course_for_user,
# )

# from app.core.database import DatabaseManager


# @pytest.mark.asyncio
# async def test_get_validated_course_happy_path(
#     user_in_neo4j_db: neo.User,
#     course_in_neo4j_db: neo.Course,
#     test_db_manager: DatabaseManager,
# ):
#     neo_driver = test_db_manager.neo4j_driver

#     user_id = user_in_neo4j_db.user_id
#     print(user_id)
#     course_id = course_in_neo4j_db.course_id

#     print("test")
#     try:
#         await get_validated_course_for_user(neo_driver, user_id, course_id)

#     except Exception as e:
#         pytest.fail(f"happy path test failed: {e}")


# @pytest.mark.asyncio
# async def test_get_random_question_happy_path(
#     course_in_neo4j_db: neo.Course,
#     user_in_neo4j_db: neo.User,
#     questions_in_neo4j_db: tuple[neo.MultipleChoice, neo.FillInBlank],
#     test_db_manager: DatabaseManager,
# ):
#     neo_driver = test_db_manager.neo4j_driver

#     user_id = user_in_neo4j_db.user_id
#     course_id = course_in_neo4j_db.course_id

#     mcq, fib = questions_in_neo4j_db
#     possible_question_ids = {
#         str(mcq.question_id),
#         str(fib.question_id),
#     }

#     result_question: dict[str, Any] = {}

#     try:
#         result_question["question_id"] = await get_random_question_for_user(
#             neo_driver=neo_driver,
#             user_id=user_id,
#             course_id=course_id,
#         )

#     except Exception as e:
#         pytest.fail(f"happy path test failed: {e}")
