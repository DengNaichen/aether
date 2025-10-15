# from typing import LiteralString
# from uuid import UUID
# from neo4j import AsyncDriver
#
#
# async def enroll_user_to_course_in_neo4j(
#         driver: AsyncDriver,
#         user_id: UUID,
#         course_id: str,
# ):
#     query: LiteralString = """
#     // 1. create the user node
#     MERGE (u:User {UserId: $user_id})
#     // 2. find or create the course node
#     MERGE (c:Course {CourseId: $course_id})
#     // 3. find or create the relationship between user and course
#     MERGE(u)-[r:ENROLLED_IN]->(c)
#     // 4. return a the relationship as
#     RETURN count(r) > 0 AS success
#     """
#     async with driver.session() as session:
#         result = await session.run(query,
#                                    user_id=str(user_id),
#                                    course_id=course_id
#                                    )
#         record = await result.single()
#         return record and record['success']
#
#
# async def unenroll_user_in_neo4j(
#         driver: AsyncDriver,
#         user_id: UUID,
#         course_id: str
# ):
#     query: LiteralString = """MATCH (u:User {userId: $user_id})-
#     [r:ENROLLED_IN]->(c:Course {courseId: $course_id}) DELETE r"""
#     async with driver.session() as session:
#         await session.run(query, user_id=str(user_id), course_id=course_id)
