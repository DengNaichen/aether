"""
Cleanup demo data from Neo4j.

This script removes all the demo data created by setup_demo_data.py

Usage:
    python scripts/cleanup_demo_data.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import DatabaseManager
from app.core.config import settings
import app.models.neo4j_model as neo


async def cleanup_data(db_manager: DatabaseManager):
    """Remove all demo data."""
    print("\n" + "=" * 80)
    print("🗑️  CLEANING UP DEMO DATA")
    print("=" * 80)

    async with db_manager.neo4j_scoped_connection():
        # Count before deletion
        courses = await asyncio.to_thread(lambda: list(neo.Course.nodes.all()))
        nodes = await asyncio.to_thread(lambda: list(neo.KnowledgeNode.nodes.all()))
        questions = await asyncio.to_thread(lambda: list(neo.MultipleChoice.nodes.all()))

        print(f"\n📊 Current data:")
        print(f"   Courses: {len(courses)}")
        print(f"   Knowledge Nodes: {len(nodes)}")
        print(f"   Questions: {len(questions)}")

        if len(courses) == 0 and len(nodes) == 0 and len(questions) == 0:
            print(f"\n✅ No data to clean up!")
            return

        response = input(f"\n⚠️  This will DELETE all the above data. Continue? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("❌ Cancelled.")
            return

        # Delete questions first (to avoid orphaned relationships)
        print(f"\n🗑️  Deleting questions...")
        for q in questions:
            await asyncio.to_thread(q.delete)
        print(f"   ✅ Deleted {len(questions)} questions")

        # Delete knowledge nodes
        print(f"\n🗑️  Deleting knowledge nodes...")
        for node in nodes:
            await asyncio.to_thread(node.delete)
        print(f"   ✅ Deleted {len(nodes)} knowledge nodes")

        # Delete courses
        print(f"\n🗑️  Deleting courses...")
        for course in courses:
            await asyncio.to_thread(course.delete)
        print(f"   ✅ Deleted {len(courses)} courses")

    print("\n" + "=" * 80)
    print("✅ CLEANUP COMPLETED SUCCESSFULLY!")
    print("=" * 80 + "\n")


async def main():
    """Main cleanup function."""
    print(f"\nEnvironment: {settings.ENVIRONMENT}")
    print(f"Neo4j URI: {settings.NEO4J_URI}")

    db_manager = DatabaseManager(settings)

    try:
        await cleanup_data(db_manager)
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
