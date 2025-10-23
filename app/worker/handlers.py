from neomodel import DoesNotExist

from app.worker.config import WorkerContext, register_handler
import asyncio
from neomodel.exceptions import NeomodelException, RequiredProperty

import app.models.neo4j_model as neo


def _create_or_update_course_sync(
        course_id: str,
        course_name: str
) -> tuple[neo.Course, bool]:

    try:
        course_node = neo.Course.nodes.get(course_id=course_id)
        created = False
        print(f"Node found: {course_id}")

    except DoesNotExist:
        print(f"Node not found, creating: {course_id}")  # 调试日志
        course_node = neo.Course(course_id=course_id,
                                 course_name=course_name).save()
        created = True

    if not created and not course_name != course_node.course_name:
        print(f"Node found, updating name for: {course_id}")
        course_node.course_name = course_name
        course_node.save()

    return course_node, created


@register_handler("handle_neo4j_create_course")
async def handle_neo4j_create_course(
        payload: dict,
        ctx: WorkerContext,
):
    course_id = payload.get("course_id")
    course_name = payload.get("course_name")

    if not all([course_id, course_name]):
        raise ValueError(
            f"Invalid payload: missing course_id or course_name. "
            f"Payload: {payload}"
        )

    try:
        async with ctx.neo4j_scoped_connection():
            course_node, created = await asyncio.to_thread(
                _create_or_update_course_sync,
                course_id,
                course_name
            )
        status = "created" if created else "updated"
        print(f"✅ Course '{course_node.course_name}' "
              f"({course_node.course_id}) {status} in graph database")

    except (RequiredProperty, NeomodelException) as e:
        print(f"❌ Graph database operation failed for payload {payload}."
              f" Error: {e}")
    except Exception as e:
        print(
            f"❌ An unexpected error occurred for payload {payload}. Error: {e}")


def _enroll_user_in_course_sync(
        user_id: str,
        user_name: str,
        course_id: str,
) -> tuple[neo.User, bool]:

    try:
        course_node = neo.Course.nodes.get(course_id=course_id)
    except DoesNotExist:
        raise ValueError(f" Course '{course_id}' does not exist.")

    # check if user existing
    try:
        user_node = neo.User.nodes.get(user_id=user_id)
        created = False
    except DoesNotExist:
        user_node = neo.User(user_id=user_id, user_name=user_name).save()
        created = True

    if not created and user_node.name != user_name:
        # if the user already existed, will update the information
        user_node.user_name = user_name
        user_node.save()

    user_node.enrolled_course.connect(course_node)

    return user_node, created


@register_handler("handle_neo4j_enroll_a_student_in_a_course")
async def handle_neo4j_enroll_a_student_in_a_course(
        payload: dict,
        ctx: WorkerContext
):
    """
    """
    course_id = payload.get("course_id")
    user_id = payload.get("user_id")
    user_name = payload.get("user_name")

    if not all([course_id, user_id, user_name]):
        raise ValueError("❌, 缺少必要的参数: course_id, user_id, 或 user_name。")

    try:
        async with ctx.neo4j_scoped_connection():
            await asyncio.to_thread(
                _enroll_user_in_course_sync,
                user_id,
                user_name,
                course_id,
            )
        print(f"✅ Successfully enrolled student {user_id} "
              f"in course {course_id} ")

    except ValueError as e:
        print(f"❌, enrollment failed: {e}")

    except Exception as e:
        print(f"❌, unknown error when enrolling student {user_id} ")


# @register_handler("handle_neo4j_create_knowledge_node")
# async def handle_neo4j_create_knowledge_node(payload: dict, ctx: WorkerContext):
#     knowledge_node_id = payload.get("knowledge_node_id")
#     course_id = payload.get("course_id")
#
#     if not knowledge_node_id:
#         raise ValueError(f"Missing knowledge node id: {knowledge_node_id} "
#                          f"for graph database sync")
#     if not course_id:
#         raise ValueError(f"Missing course id: {course_id} ")
#
#     async with ctx.neo4j_session() as session:
#         await session.execute_write(
#             lambda tx: tx.run(
#                 """
#                  MERGE (kn: KnowledgeNode {id: $kn_id})})
#                  MERGE (c: Course {id: $course_id})
#                  MERGE(kn)-[r:BELONG_TO]->(c)
#                  RETURN count(r) > 0 AS success
#                 """,
#                 kn_id=knowledge_node_id,
#                 course_id=course_id,
#             )
#         )
#     print(f"✅ knowledge node {knowledge_node_id} synced to graph database")


# @register_handler("handle_neo4j_create_knowledge_relation")
# async def handle_neo4j_create_knowledge_relation(
#         payload: dict, ctx: WorkerContext
# ):
#     course_id = payload.get("course_id")
#     source_node_id = payload.get("source_node_id")
#     target_node_id = payload.get("target_node_id")
#     relation_type = payload.get("relation_type")
#
#     if not all([course_id, source_node_id, target_node_id, relation_type]):
#         raise ValueError(f"Missing one or more required parameters.")
#
#     query = (
#         f"MATCH (sn:KnowledgeNode {{id: $sn_id}}) "
#         f"MATCH (tn:KnowledgeNode {{id: $tn_id}}) "
#         f"MERGE (sn)-[r:{relation_type}]->(tn)"
#     )
#
#     async with ctx.neo4j_session() as session:
#         await session.execute_write(
#             lambda tx: tx.run(
#                 query,
#                 sn_id=source_node_id,
#                 tn_id=target_node_id,
#             )
#         )
#     print(f"✅ Knowledge relation '{relation_type}' between source node "
#           f"'{source_node_id}' and target node '{target_node_id}' "
#           f"synced to graph database")


# @register_handler("handle_neo4j_create_question")
# async def handle_neo4j_create_question(payload: dict, ctx: WorkerContext):
#     question_id = payload.get("question_id")
#     question_type = payload.get("question_type")
#     difficulty = payload.get("difficulty")
#     knowledge_node_id = payload.get("knowledge_node_id")
#
#     if not all([question_id, question_type, difficulty, knowledge_node_id]):
#         raise ValueError(f"Missing one or more required parameters.")
#
#     query = (
#         f"MATCH (q:Question {{id: $question_id}}) "
#         f"MATCH (kn:KnowledgeNode {{id: knowledge_node_id}}) "
#         f"SET q:{question_type}:{difficulty} "
#         f"MERGE (q)-[r:TESTS]->(kn)"
#     )
#     async with ctx.neo4j_session() as session:
#         await session.execute_write(
#             lambda tx: tx.run(
#                 query,
#                 question_id=question_id,
#                 knowledge_node_id=knowledge_node_id,
#             ).consume()
#         )
#     print(f"✅ question {question_id} synced to graph database")


# @register_handler("handle_neo4j_update_knowledge_node")
# async def handle_neo4j_update_knowledge_node(payload: dict, ctx: WorkerContext):
#     pass


# @register_handler("handle_neo4j_update_question")
# async def handle_neo4j_update_question(payload: dict, ctx: WorkerContext):
#     pass
#
#
# @register_handler("handle_neo4j_update_mastery_level")
# async def handle_neo4j_update_mastery_level(payload: dict, ctx: WorkerContext):
#     pass
#
#
@register_handler("handle_neo4j_query_problem")
async def handle_neo4j_query_problem(payload: dict, ctx: WorkerContext):
    pass
