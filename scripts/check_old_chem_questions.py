
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import select, func

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load env
env_file = project_root / ".env.local"
if env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv()

from app.core.database import db_manager
from app.models.knowledge_graph import KnowledgeGraph
from app.models.question import Question

async def check_old_questions():
    print("Checking for old Grade 11 Chemistry questions...")
    try:
        await db_manager.initialize()
        
        async with db_manager.get_sql_session() as session:
            # Find all graphs with "chemistry" in the name
            stmt = select(KnowledgeGraph).where(
                KnowledgeGraph.name.ilike('%chemistry%')
            ).order_by(KnowledgeGraph.created_at.desc())
            
            result = await session.execute(stmt)
            graphs = result.scalars().all()
            
            print(f"\nFound {len(graphs)} graph(s) with 'chemistry' in name:\n")
            
            for graph in graphs:
                # Count questions for this graph
                q_stmt = select(func.count(Question.id)).where(
                    Question.graph_id == graph.id
                )
                q_count = await session.scalar(q_stmt)
                
                print(f"Graph: {graph.name}")
                print(f"  ID: {graph.id}")
                print(f"  Slug: {graph.slug}")
                print(f"  Created: {graph.created_at}")
                print(f"  Questions: {q_count}")
                print(f"  is_template: {graph.is_template}")
                print()

    except Exception as e:
        print(f"❌ Check failed: {e}")
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(check_old_questions())
