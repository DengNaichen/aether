from sqlalchemy.future import select
# from app.models.models import Student
# from app.schemas.schemas import StudentCreate
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.models.student import Student
from app.core.security import get_password_hash
from app.core.config import settings
from app.core.database import neo4j_driver

from src.app.schemas.student import StudentCreate


async def get_student_by_email(db: AsyncSession, email: str)-> Student | None:
    """check the student based on email"""
    # result = await db.execute(select(Student).where(Student.email) == email)
    # return result.scalars().first()
    # statement = select(Student).where(Student.email == email)
    #
    # # ADD THIS DEBUGGING LINE
    # print(f"DEBUG: The statement passed to db.execute is: {repr(statement)}")
    #
    # result = await db.execute(statement)
    # return result.scalar_one_or_none()
    statement = select(Student).where(Student.email == email)
    result = await db.execute(statement)
    return result.scalars().first()


async def create_student(student_data: StudentCreate, db: AsyncSession) -> Student:
    # hash the password
    hashed_password = get_password_hash(student_data.password)
    new_student = Student(
        name=student_data.name,
        email=student_data.email,
        hashed_password=hashed_password,
    )
    db.add(new_student)
    await db.commit()
    await db.refresh(new_student)
    return new_student
