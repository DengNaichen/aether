#!/usr/bin/env python3
"""
Clean up development course data

WARNING: This script will delete the g10_phys course and all related data!
Including: knowledge nodes, relationships, questions, etc.
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
from neomodel import DoesNotExist

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
This operation will delete the following data:

  Course ID: {COURSE_ID}
  Course Name: Grade 11 Physics - Chapter 1: Kinematics

  Will delete:
  - PostgreSQL course record
  - Neo4j course node
  - All associated knowledge nodes
  - All associated questions
  - All associated relationships

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
                return 0, 0, 0

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

            print(f"\nFound data:")
            print(f"  Knowledge nodes: {node_count}")
            print(f"  Questions: {question_count}")

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

            # Delete course
            print(f"\nDeleting course node...")
            course.delete()
            print(f"✅ Deleted course {COURSE_ID}")

            return node_count, question_count, 1

        return await asyncio.to_thread(_delete)


async def delete_from_postgres():
    """Delete course from PostgreSQL"""
    print_section("Cleaning PostgreSQL data")

    async with db_manager.get_sql_session() as session:
        course = await session.get(Course, COURSE_ID)

        if not course:
            print(f"ℹ️  Course {COURSE_ID} does not exist in PostgreSQL")
            return False

        print(f"Found course: {course.name}")
        print(f"Deleting...")

        await session.delete(course)
        await session.commit()

        print(f"✅ Successfully deleted course {COURSE_ID}")
        return True


async def main():
    """Main function"""
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
        node_count, question_count, course_count = await delete_from_neo4j()

        # Delete from PostgreSQL
        postgres_deleted = await delete_from_postgres()

        # Summary
        print_section("Completed")
        print(f"""
✅ Cleanup completed!

Deleted:
  - Neo4j:
    * Course nodes: {course_count}
    * Knowledge nodes: {node_count}
    * Questions: {question_count}
  - PostgreSQL:
    * Course records: {'1' if postgres_deleted else '0'}

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
