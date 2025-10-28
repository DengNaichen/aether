"""Quick setup demo data without confirmation."""
import asyncio
import sys
from pathlib import Path
import shutil
from tempfile import NamedTemporaryFile

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
    print("\n🚀 Setting up demo data in Neo4j...")
    print(f"Environment: {settings.ENVIRONMENT}")
    
    db_manager = DatabaseManager(settings)
    
    try:
        # Create courses
        print("\n📚 Creating courses...")
        async with db_manager.neo4j_scoped_connection():
            for cid, cname in [("g10_phys", "Grade 10 Physics"), ("g10_chem", "Grade 10 Chemistry")]:
                course = neo.Course(course_id=cid, course_name=cname)
                await asyncio.to_thread(course.save)
                print(f"   ✅ {cid}")
        
        worker_ctx = WorkerContext(db_mng=db_manager)
        
        # Import nodes
        print("\n📦 Importing nodes...")
        temp = NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        shutil.copy(EXAMPLE_DATA_DIR / "nodes.csv", temp.name)
        temp.close()
        result = await handle_bulk_import_nodes({"file_path": temp.name, "requested_by": "demo"}, worker_ctx)
        print(f"   ✅ {result['successful']} nodes")
        
        # Import relationships
        print("\n🔗 Importing relationships...")
        temp = NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        shutil.copy(EXAMPLE_DATA_DIR / "relationships.csv", temp.name)
        temp.close()
        result = await handle_bulk_import_relations({"file_path": temp.name, "requested_by": "demo"}, worker_ctx)
        print(f"   ✅ {result['successful']} relationships")
        
        # Import questions
        print("\n❓ Importing questions...")
        temp = NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        shutil.copy(EXAMPLE_DATA_DIR / "questions.csv", temp.name)
        temp.close()
        result = await handle_bulk_import_question({"file_path": temp.name, "requested_by": "demo"}, worker_ctx)
        print(f"   ✅ {result['successful']} questions")
        
        print("\n✅ Demo data created successfully!")
        print(f"\n🌐 View in Neo4j Browser: http://localhost:7474")
        print(f"   Try: MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 100")
        
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
