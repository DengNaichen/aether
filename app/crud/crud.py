from typing import List, Sequence
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.user import User
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.knowledge_node import KnowledgeNode


async def check_course_exist(course_id: str, db: AsyncSession) -> bool:
    stmt = select(Course).where(Course.id == course_id)
    result = await db.execute(stmt)
    existing_course = result.scalar_one_or_none()

    return existing_course is not None


async def check_knowledge_node(
        knowledge_node_id: str,
        db: AsyncSession
) -> bool:
    stmt = select(KnowledgeNode).where(KnowledgeNode.id == knowledge_node_id)
    result = await db.execute(stmt)
    existing_knowledge_node = result.scalar_one_or_none()

    return existing_knowledge_node is not None


async def get_all_course(
        db: AsyncSession,
) -> Sequence[Course]:
    """ Get all courses in a database
    Args:
        db: AsyncSession
    Returns:
        Sequence[Course]: list of all courses in the database
    """
    result = await db.execute(select(Course))
    return result.scalars().all()


async def get_user_enrollments_for_courses(
        db: AsyncSession,
        course_ids: List[str],
        user_id: uuid.UUID,
):
    """Fetches the set of courses a user if enrolled in from a given list

    This function queries the database to find all course IDs from a provided
    list that a specific user is enrolled in. It is designed as a bulk
    operation to avoid the N+1 query problem.

    Args:
         db: AsyncSession
         course_ids: list of course id to check for enrollments.
         user_id: the ID of the user whose enrollments are to be checked
    Returns:
         A set containing the course IDs from the input list for which
         the user is enrolled.
    """
    stmt = (
        select(Enrollment.course_id)
        .where(
            Enrollment.user_id == user_id,
            Enrollment.course_id.in_(course_ids),
        )
    )
    result = await db.execute(stmt)
    # Returning a set provides fast O(1) average time complexity for lookups.
    return set(result.scalars().all())


async def get_knowledge_node_counts_for_courses(
        course_ids: List[str],
        db: AsyncSession,
):
    """ Gets the number of knowledge nodes for a list of courses.

    This function count the number of knowledge nodes associated with each
    course in a given list. It used a SQL GROUP BY clause to aggregate the
    counts for all specified courses at once.

    Args:
        course_ids: A list of course id for which to count knowledge nodes.
        db: AsyncSession

    Returns:
        A dictionary mapping course ID to its corresponding count of knowledge
        nodes. Course with no knowledge nodes will be omitted from the result.
    """
    stmt = (
        select(KnowledgeNode.course_id, func.count(KnowledgeNode.id))
        .where(KnowledgeNode.course_id.in_(course_ids))
        .group_by(KnowledgeNode.course_id)
    )
    result = await db.execute(stmt)
    return dict((row[0], row[1]) for row in result)


async def get_knowledge_node_num_of_a_course(
        course_id: str,
        db: AsyncSession
) -> int:
    """ Check knowledge node number of a course
    Args:
        course_id: the id of the course to check
        db: the database session
    Return:
        The number of knowledge nodes this course has
    """
    stmt = (
        select(func.count(KnowledgeNode.id))
        .where(KnowledgeNode.course_id == course_id)
    )
    result = await db.execute(stmt)
    count = result.scalar_one()
    return count


async def check_enrollment(
        course_id: str,
        current_user: User,
        db: AsyncSession
) -> bool:
    """
    Check if a course is enrolled by a given user
    Args:
        course_id: the id of the course to check
        current_user: the current user
        db: the database session
    return:
        bool: true if the course is enrolled by the user, false otherwise
    """
    stmt = select(Enrollment).where(
        Enrollment.course_id == course_id,
        Enrollment.user_id == current_user.id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None
