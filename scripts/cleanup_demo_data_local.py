"""Cleanup demo data from local Neo4j."""
import asyncio
import os
import sys
from pathlib import Path

os.environ['ENVIRONMENT'] = 'test'

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import DatabaseManager
from app.core.config import settings
import app.models.neo4j_model as neo

async def main():
    print("\n" + "=" * 80)
    print("🗑️  CLEANING UP DEMO DATA FROM NEO4J")
    print("=" * 80)
    
    db_manager = DatabaseManager(settings)
    
    try:
        async with db_manager.neo4j_scoped_connection():
            courses = await asyncio.to_thread(lambda: list(neo.Course.nodes.all()))
            nodes = await asyncio.to_thread(lambda: list(neo.KnowledgeNode.nodes.all()))
            questions = await asyncio.to_thread(lambda: list(neo.MultipleChoice.nodes.all()))
            
            print(f"\n📊 Current data in Neo4j:")
            print(f"   Courses: {len(courses)}")
            print(f"   Knowledge Nodes: {len(nodes)}")
            print(f"   Questions: {len(questions)}")
            
            if len(courses) == 0 and len(nodes) == 0 and len(questions) == 0:
                print(f"\n✅ Database is already empty!")
                return
            
            print(f"\n🗑️  Deleting {len(questions)} questions...")
            for q in questions:
                await asyncio.to_thread(q.delete)
            
            print(f"🗑️  Deleting {len(nodes)} knowledge nodes...")
            for node in nodes:
                await asyncio.to_thread(node.delete)
            
            print(f"🗑️  Deleting {len(courses)} courses...")
            for course in courses:
                await asyncio.to_thread(course.delete)
            
            print("\n" + "=" * 80)
            print("✅ ALL DEMO DATA DELETED SUCCESSFULLY!")
            print("=" * 80 + "\n")
    
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
