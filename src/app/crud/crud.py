from sqlalchemy.future import select

# from app.core.config import settings
# from app.core.database import neo4j_driver
#
#
# async def enroll_student_in_course(
#         student: Student,
#         course_name: str
# ):
#     """
#     Create a student node in a certain Neo4j database
#     """
#     db_name = settings.COURSE_TO_NEO4J_DB.get(course_name)
#     if not db_name:
#         raise ValueError(f"Invalid course name: {course_name}")
#
#     async with neo4j_driver.session(database=db_name) as session:
#         query = """
#         MERGE (s: Student {id: $id})
#         ON CREATE SET
#             s.name = $name,
#             s.email = $email,
#             s.createdAt = $createdAt
#         ON MATCH SET
#             s.name = $name,
#             s.email = $email
#         RETURN s
#         """
#         await session.run(
#             query,
#             id=str(student.id),
#             name=student.name,
#             email=student.email,
#             createdAt=student.createdAt
#         )
#     return {"message": f"Student {student.id} enrolled in {course_name}"}
