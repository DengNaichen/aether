from sqlalchemy.future import select

from app.models.models import Student
from app.schemas.schemas import StudentCreate
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_password_hash
from app.core.config import settings
from app.core.database import neo4j_driver


# async def get_student_by_email(db: AsyncSession, email: str) -> Student | None:
#     """check student based on email address"""
#     result = await db.execute(select(Student).where(Student.email == email))
#     return result.scalars().first()
#
#
# async def create_student(student_data: StudentCreate, db: AsyncSession) -> Student:
#     # hash the password
#     hashed_password = get_password_hash(student_data.password)
#
#     new_student = Student(
#         name=student_data.name,
#         email=student_data.email,
#         password_hashed=hashed_password
#     )
#
#     db.add(new_student)
#     await db.commit()
#     await db.refresh(new_student)
#     return new_student


async def enroll_student_in_course(
        student: Student,
        course_name: str
):
    """
    Create a student node in a certain Neo4j database
    """
    db_name = settings.COURSE_TO_NEO4J_DB.get(course_name)
    if not db_name:
        raise ValueError(f"Invalid course name: {course_name}")

    async with neo4j_driver.session(database=db_name) as session:
        query = """
        MERGE (s: Student {id: $id})
        ON CREATE SET
            s.name = $name,
            s.email = $email,
            s.createdAt = $createdAt
        ON MATCH SET
            s.name = $name,
            s.email = $email
        RETURN s
        """
        await session.run(
            query,
            id=str(student.id),
            name=student.name,
            email=student.email,
            createdAt=student.createdAt
        )
    return {"message": f"Student {student.id} enrolled in {course_name}"}
