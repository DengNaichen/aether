#!/usr/bin/env python3
"""
Clean up development data, include all data in Postgres and Neo4j
Course
User
Enrollment
Quiz Submission Record.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import db_manager
# Import all models to avoid SQLAlchemy mapping errors
from app.models import Base, User, Course, Enrollment
from app.models import quiz  # Import quiz module for QuizAttempt
import app.models.neo4j_model as neo
from neomodel import DoesNotExist, db as neomodel_db

COURSE_ID = "g10_phys"


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


async def confirm_deletion():
    """Confirm deletion operation"""
    print_section("⚠️  Warning")
    print(f"""
This operation will delete ALL data:

  Course ID: {COURSE_ID}
  Course Name: Grade 11 Physics - Chapter 1: Kinematics

  Will delete:
  - PostgreSQL: course record, enrollments, quiz attempts, users
  - Neo4j: course node, knowledge nodes, questions, users
  - Neo4j: ALL relationships (HAS_MASTERY, HAS_SUBTOPIC, IS_PREREQUISITE_FOR, etc.)

This operation cannot be undone!
""")

    response = input("Confirm deletion? (yes/no): ").strip().lower()
    return response == "yes"


async def delete_from_neo4j():
    """Delete course and related data from Neo4j"""
    print_section("Cleaning Neo4j data")

    async with db_manager.neo4j_scoped_connection():
        def _delete():
            from neomodel import db as neomodel_db

            # Check if course exists
            course = neo.Course.nodes.get_or_none(course_id=COURSE_ID)
            if not course:
                print(f"ℹ️  Course {COURSE_ID} does not exist in Neo4j")
                return 0, 0, 0, 0, 0

            # Count before deletion
            result = neomodel_db.cypher_query(
                "MATCH (c:Course {course_id: $course_id})<-[:BELONGS_TO]-(n:KnowledgeNode) RETURN count(n)",
                {"course_id": COURSE_ID}
            )
            node_count = result[0][0][0] if result[0] else 0

            result = neomodel_db.cypher_query(
                """
                MATCH (c:Course {course_id: $course_id})<-[:BELONGS_TO]-(n:KnowledgeNode)
                <-[:TESTS]-(q:MultipleChoice)
                RETURN count(q)
                """,
                {"course_id": COURSE_ID}
            )
            question_count = result[0][0][0] if result[0] else 0

            # Count HAS_MASTERY relationships
            result = neomodel_db.cypher_query(
                "MATCH ()-[r:HAS_MASTERY]->() RETURN count(r)"
            )
            mastery_count = result[0][0][0] if result[0] else 0

            # Count users
            result = neomodel_db.cypher_query(
                "MATCH (u:User) RETURN count(u)"
            )
            user_count = result[0][0][0] if result[0] else 0

            print(f"\nFound data:")
            print(f"  Knowledge nodes: {node_count}")
            print(f"  Questions: {question_count}")
            print(f"  HAS_MASTERY relationships: {mastery_count}")
            print(f"  Users: {user_count}")

            # Delete HAS_MASTERY relationships first
            if mastery_count > 0:
                print(f"\nDeleting {mastery_count} HAS_MASTERY relationships...")
                neomodel_db.cypher_query(
                    "MATCH ()-[r:HAS_MASTERY]->() DELETE r"
                )
                print(f"✅ Deleted {mastery_count} HAS_MASTERY relationships")

            # Delete questions first (they depend on knowledge nodes)
            if question_count > 0:
                print(f"\nDeleting {question_count} questions...")
                result = neomodel_db.cypher_query(
                    """
                    MATCH (c:Course {course_id: $course_id})<-[:BELONGS_TO]-(n:KnowledgeNode)
                    <-[:TESTS]-(q:MultipleChoice)
                    DETACH DELETE q
                    RETURN count(q)
                    """,
                    {"course_id": COURSE_ID}
                )
                print(f"✅ Deleted {question_count} questions")

            # Delete knowledge nodes (relationships will be automatically deleted)
            if node_count > 0:
                print(f"\nDeleting {node_count} knowledge nodes...")
                result = neomodel_db.cypher_query(
                    """
                    MATCH (c:Course {course_id: $course_id})<-[:BELONGS_TO]-(n:KnowledgeNode)
                    DETACH DELETE n
                    RETURN count(n)
                    """,
                    {"course_id": COURSE_ID}
                )
                print(f"✅ Deleted {node_count} knowledge nodes (and all their relationships)")

            # Delete users
            if user_count > 0:
                print(f"\nDeleting {user_count} users...")
                neomodel_db.cypher_query(
                    "MATCH (u:User) DETACH DELETE u"
                )
                print(f"✅ Deleted {user_count} users")

            # Delete course
            print(f"\nDeleting course node...")
            course.delete()
            print(f"✅ Deleted course {COURSE_ID}")

            return node_count, question_count, mastery_count, user_count, 1

        return await asyncio.to_thread(_delete)


async def delete_from_postgres():
    """Delete course from PostgreSQL"""
    print_section("Cleaning PostgreSQL data")

    async with db_manager.get_sql_session() as session:
        course = await session.get(Course, COURSE_ID)

        if not course:
            print(f"ℹ️  Course {COURSE_ID} does not exist in PostgreSQL")
            return 0, 0, 0, False

        print(f"Found course: {course.name}")

        # Delete related data first (foreign key constraints)
        from sqlalchemy import delete, select
        from app.models.quiz import QuizAttempt, SubmissionAnswer

        # Delete submission answers first (depends on quiz_attempts)
        submission_answers_stmt = delete(SubmissionAnswer).where(
            SubmissionAnswer.submission_id.in_(
                select(QuizAttempt.attempt_id).where(QuizAttempt.course_id == COURSE_ID)
            )
        )
        result = await session.execute(submission_answers_stmt)
        submission_answer_count = result.rowcount
        if submission_answer_count > 0:
            print(f"Deleting {submission_answer_count} submission answer(s)...")

        # Delete quiz attempts (depends on user and course)
        quiz_attempts_stmt = delete(QuizAttempt).where(QuizAttempt.course_id == COURSE_ID)
        result = await session.execute(quiz_attempts_stmt)
        quiz_attempt_count = result.rowcount
        if quiz_attempt_count > 0:
            print(f"Deleting {quiz_attempt_count} quiz attempt(s)...")

        # Delete enrollments (depends on user and course)
        enrollments_stmt = delete(Enrollment).where(Enrollment.course_id == COURSE_ID)
        result = await session.execute(enrollments_stmt)
        enrollment_count = result.rowcount
        if enrollment_count > 0:
            print(f"Deleting {enrollment_count} enrollment(s)...")

        # Now safe to delete users (no more foreign key dependencies)
        user_count_result = await session.execute(select(User))
        user_count = len(user_count_result.scalars().all())
        if user_count > 0:
            print(f"Deleting {user_count} user(s)...")
            users_stmt = delete(User)
            await session.execute(users_stmt)

        print(f"Deleting course...")
        await session.delete(course)
        await session.commit()

        print(f"✅ Successfully deleted course {COURSE_ID}")
        if user_count > 0:
            print(f"✅ Deleted {user_count} user(s)")
        if quiz_attempt_count > 0:
            print(f"✅ Deleted {quiz_attempt_count} quiz attempt(s)")
        if enrollment_count > 0:
            print(f"✅ Deleted {enrollment_count} enrollment(s)")
        return user_count, quiz_attempt_count, enrollment_count, True


async def main():
    """Main function"""
    from pathlib import Path

    env_local_path = Path(__file__).parent.parent / ".env.local"
    if not env_local_path.exists():
        print("\n" + "="*60)
        print("🚫 ERROR: This script can only run with .env.local!")
        print("   .env.local file not found")
        print("   This is a safety measure to prevent production data deletion")
        print("="*60 + "\n")
        sys.exit(1)

    print(f"✅ Using .env.local configuration\n")

    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║        Development Environment Data Cleanup                ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
""")

    try:
        # Confirm deletion
        if not await confirm_deletion():
            print("\n❌ Operation cancelled")
            return

        # Delete from Neo4j (must be first, as it has more dependencies)
        node_count, question_count, mastery_count, neo_user_count, course_count = await delete_from_neo4j()

        # Delete from PostgreSQL
        pg_user_count, quiz_attempt_count, enrollment_count, postgres_deleted = await delete_from_postgres()

        # Summary
        print_section("Completed")
        print(f"""
✅ Cleanup completed!

Deleted:
  - Neo4j:
    * Course nodes: {course_count}
    * Knowledge nodes: {node_count}
    * Questions: {question_count}
    * HAS_MASTERY relationships: {mastery_count}
    * Users: {neo_user_count}
  - PostgreSQL:
    * Course records: {'1' if postgres_deleted else '0'}
    * Quiz attempts: {quiz_attempt_count}
    * Enrollments: {enrollment_count}
    * Users: {pg_user_count}

You can now run setup_dev_course.py to load fresh course data.
""")

    except Exception as e:
        print_section("Error")
        print(f"❌ Cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
