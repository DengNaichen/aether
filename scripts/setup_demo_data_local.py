"""Setup demo data in local Neo4j using test environment."""
import asyncio
import os
import sys
from pathlib import Path
import shutil
from tempfile import NamedTemporaryFile

# Force test environment
os.environ['ENVIRONMENT'] = 'test'

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import DatabaseManager
from app.core.config import settings
from app.worker.bulk_import_handlers import (
    handle_bulk_import_nodes,
    handle_bulk_import_question,
    handle_bulk_import_relations,
)
from app.worker.config import WorkerContext
import app.models.neo4j_model as neo

EXAMPLE_DATA_DIR = project_root / "example_data"

async def main():
    print("\n" + "=" * 80)
    print("🚀 SETTING UP DEMO DATA IN LOCAL NEO4J")
    print("=" * 80)
    print(f"\nEnvironment: {settings.ENVIRONMENT}")
    print(f"Neo4j URI: {settings.NEO4J_URI}")
    print(f"Neo4j Database: {settings.NEO4J_DATABASE}")
    
    print("\n📋 This will create:")
    print("   • 2 Courses (Physics G10, Chemistry G10)")
    print("   • 15 Knowledge Nodes")
    print("   • 20 Relationships")
    print("   • 4 Sample Questions")
    
    print("\n⚠️  Data will PERSIST in your local Neo4j until you delete it.")
    print("   To clean up: python scripts/cleanup_demo_data_local.py")
    
    db_manager = DatabaseManager(settings)
    
    try:
        # Create courses
        print("\n" + "=" * 80)
        print("📚 STEP 1: Creating Courses")
        print("=" * 80)
        async with db_manager.neo4j_scoped_connection():
            for cid, cname in [("g10_phys", "Grade 10 Physics"), ("g10_chem", "Grade 10 Chemistry")]:
                existing = await asyncio.to_thread(neo.Course.nodes.get_or_none, course_id=cid)
                if existing:
                    print(f"   ✅ Course exists: {cid}")
                else:
                    course = neo.Course(course_id=cid, course_name=cname)
                    await asyncio.to_thread(course.save)
                    print(f"   ✅ Created: {cid} - {cname}")
        
        worker_ctx = WorkerContext(db_mng=db_manager)
        
        # Import nodes
        print("\n" + "=" * 80)
        print("📦 STEP 2: Importing Knowledge Nodes")
        print("=" * 80)
        temp = NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        shutil.copy(EXAMPLE_DATA_DIR / "nodes.csv", temp.name)
        temp.close()
        result = await handle_bulk_import_nodes({"file_path": temp.name, "requested_by": "demo"}, worker_ctx)
        print(f"\n📊 Result: {result['successful']} successful, {result['failed']} failed")
        
        # Import relationships
        print("\n" + "=" * 80)
        print("🔗 STEP 3: Importing Relationships")
        print("=" * 80)
        temp = NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        shutil.copy(EXAMPLE_DATA_DIR / "relationships.csv", temp.name)
        temp.close()
        result = await handle_bulk_import_relations({"file_path": temp.name, "requested_by": "demo"}, worker_ctx)
        print(f"\n📊 Result: {result['successful']} successful, {result['failed']} failed")
        
        # Import questions
        print("\n" + "=" * 80)
        print("❓ STEP 4: Importing Questions")
        print("=" * 80)
        temp = NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        shutil.copy(EXAMPLE_DATA_DIR / "questions.csv", temp.name)
        temp.close()
        result = await handle_bulk_import_question({"file_path": temp.name, "requested_by": "demo"}, worker_ctx)
        print(f"\n📊 Result: {result['successful']} successful, {result['failed']} failed")
        
        # Verify data
        print("\n" + "=" * 80)
        print("🔍 VERIFICATION")
        print("=" * 80)
        async with db_manager.neo4j_scoped_connection():
            courses = await asyncio.to_thread(lambda: list(neo.Course.nodes.all()))
            nodes = await asyncio.to_thread(lambda: list(neo.KnowledgeNode.nodes.all()))
            questions = await asyncio.to_thread(lambda: list(neo.MultipleChoice.nodes.all()))
            
            print(f"\n   📚 Courses: {len(courses)}")
            for c in courses:
                print(f"      • {c.course_id}: {c.course_name}")
            
            print(f"\n   📌 Knowledge Nodes: {len(nodes)}")
            physics = [n for n in nodes if 'phys' in n.node_id]
            chem = [n for n in nodes if 'chem' in n.node_id]
            print(f"      🔬 Physics: {len(physics)}")
            print(f"      ⚗️  Chemistry: {len(chem)}")
            
            print(f"\n   ❓ Questions: {len(questions)}")
            for q in questions:
                print(f"      • {q.question_id}: {q.text[:50]}...")
        
        # Print useful Cypher queries
        print("\n" + "=" * 80)
        print("📝 USEFUL CYPHER QUERIES (use in Neo4j Browser)")
        print("=" * 80)
        print("\n1. View all nodes and relationships:")
        print("   MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 100")
        print("\n2. View knowledge graph structure:")
        print("   MATCH (n:KnowledgeNode)-[r]->(m:KnowledgeNode) RETURN n,r,m")
        print("\n3. View physics nodes only:")
        print("   MATCH (c:Course {course_id: 'g10_phys'})<-[:BELONGS_TO]-(n:KnowledgeNode)")
        print("   OPTIONAL MATCH (n)-[r]->(m:KnowledgeNode)")
        print("   RETURN c,n,r,m")
        print("\n4. View questions with their nodes:")
        print("   MATCH (q:MultipleChoice)-[:TESTS]->(n:KnowledgeNode)")
        print("   RETURN q.question_id, q.text, q.difficulty, n.node_name")
        
        print("\n" + "=" * 80)
        print("✅ DEMO DATA CREATED SUCCESSFULLY!")
        print("=" * 80)
        print(f"\n🌐 Open Neo4j Browser: http://localhost:7474")
        print(f"   Username: neo4j")
        print(f"   Password: d1997225")
        print("\n🗑️  To clean up: python scripts/cleanup_demo_data_local.py")
        print("=" * 80 + "\n")
        
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
