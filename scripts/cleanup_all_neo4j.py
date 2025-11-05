#!/usr/bin/env python3
"""
Clean up all Neo4j database data

WARNING: This script will delete ALL data from the Neo4j database!
Including: all courses, knowledge nodes, questions, and relationships!
USE ONLY IN DEVELOPMENT ENVIRONMENT!
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


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


async def confirm_deletion():
    """Confirm deletion operation"""
    print_section("⚠️  CRITICAL WARNING")
    print("""
This operation will delete ALL data from the Neo4j database:

  - All course nodes
  - All knowledge nodes
  - All questions
  - All relationships

This operation cannot be undone! USE ONLY IN DEVELOPMENT!
""")

    response = input("Confirm deletion of ALL Neo4j data? (yes/no): ").strip().lower()
    return response == "yes"


async def get_database_stats():
    """Get database statistics"""
    async with db_manager.neo4j_scoped_connection():
        def _get_stats():
            from neomodel import db as neomodel_db

            stats = {}

            # Count courses
            result = neomodel_db.cypher_query("MATCH (c:Course) RETURN count(c)")
            stats['courses'] = result[0][0][0] if result[0] else 0

            # Get course IDs
            result = neomodel_db.cypher_query("MATCH (c:Course) RETURN c.course_id")
            stats['course_ids'] = [r[0] for r in result[0]] if result[0] else []

            # Count knowledge nodes
            result = neomodel_db.cypher_query("MATCH (n:KnowledgeNode) RETURN count(n)")
            stats['knowledge_nodes'] = result[0][0][0] if result[0] else 0

            # Count questions
            result = neomodel_db.cypher_query("MATCH (q:MultipleChoice) RETURN count(q)")
            stats['questions'] = result[0][0][0] if result[0] else 0

            return stats

        return await asyncio.to_thread(_get_stats)


async def delete_all_neo4j_data():
    """Delete all Neo4j data"""
    print_section("Cleaning Neo4j database")

    async with db_manager.neo4j_scoped_connection():
        def _delete():
            from neomodel import db as neomodel_db

            print("\nStep 1: Deleting all questions...")
            result = neomodel_db.cypher_query("MATCH (q:MultipleChoice) DETACH DELETE q RETURN count(q)")
            question_count = result[0][0][0] if result[0] else 0
            print(f"✅ Deleted {question_count} questions")

            print("\nStep 2: Deleting all knowledge nodes...")
            result = neomodel_db.cypher_query("MATCH (n:KnowledgeNode) DETACH DELETE n RETURN count(n)")
            node_count = result[0][0][0] if result[0] else 0
            print(f"✅ Deleted {node_count} knowledge nodes (and all their relationships)")

            print("\nStep 3: Deleting all courses...")
            result = neomodel_db.cypher_query("MATCH (c:Course) DETACH DELETE c RETURN count(c)")
            course_count = result[0][0][0] if result[0] else 0
            print(f"✅ Deleted {course_count} courses")

            # Verify deletion
            print("\nVerifying deletion...")
            result = neomodel_db.cypher_query("MATCH (n) RETURN count(n)")
            remaining = result[0][0][0] if result[0] else 0

            if remaining == 0:
                print(f"✅ Neo4j database is now empty")
            else:
                print(f"⚠️  Database still contains {remaining} nodes (may be other node types)")

            return course_count, node_count, question_count

        return await asyncio.to_thread(_delete)


async def main():
    """Main function"""
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║          Neo4j Complete Database Cleanup Tool              ║
║                                                            ║
║          ⚠️  DEVELOPMENT ENVIRONMENT ONLY ⚠️                ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
""")

    try:
        # Get current stats
        print_section("Current database status")
        stats = await get_database_stats()
        print(f"\n  Courses: {stats['courses']}")
        if stats['course_ids']:
            print(f"  Course IDs: {', '.join(stats['course_ids'])}")
        print(f"  Knowledge nodes: {stats['knowledge_nodes']}")
        print(f"  Questions: {stats['questions']}")

        # Confirm deletion
        if not await confirm_deletion():
            print("\n❌ Operation cancelled")
            return

        # Delete all data
        course_count, node_count, question_count = await delete_all_neo4j_data()

        # Verify final state
        print_section("Final status")
        final_stats = await get_database_stats()
        print(f"\n  Courses: {final_stats['courses']}")
        print(f"  Knowledge nodes: {final_stats['knowledge_nodes']}")
        print(f"  Questions: {final_stats['questions']}")

        print_section("Completed")
        print(f"""
✅ Cleanup completed!

Deleted:
  - Courses: {course_count}
  - Knowledge nodes: {node_count}
  - Questions: {question_count}

The Neo4j database is now clean. You can run setup_dev_course.py to load development data.
""")

    except Exception as e:
        print_section("Error")
        print(f"❌ Cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
