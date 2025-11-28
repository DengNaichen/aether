
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import select, func
from uuid import UUID

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
from app.models import KnowledgeNode, Question

GRAPH_ID = "c18d6d95-77ed-4b41-a833-dc5cddec74f4"

async def verify_questions():
    print(f"Verifying questions for graph: {GRAPH_ID}")
    try:
        await db_manager.initialize()
        
        async with db_manager.get_sql_session() as session:
            # 1. Get all nodes for the graph
            stmt = select(KnowledgeNode).where(KnowledgeNode.graph_id == UUID(GRAPH_ID))
            result = await session.execute(stmt)
            nodes = result.scalars().all()
            
            print(f"Found {len(nodes)} nodes in the graph.")
            
            nodes_with_questions = 0
            total_questions = 0
            
            print("\nSample Node Check:")
            for i, node in enumerate(nodes):
                # 2. Get questions for each node
                q_stmt = select(Question).where(Question.node_id == node.id)
                q_result = await session.execute(q_stmt)
                questions = q_result.scalars().all()
                
                count = len(questions)
                total_questions += count
                if count > 0:
                    nodes_with_questions += 1
                
                # Print first 5 nodes details
                if i < 5:
                    print(f"  - Node: {node.node_name} (ID: {node.id}) -> {count} questions")
                    for q in questions:
                        print(f"    * Q: {q.content[:50]}...")

            print("\nSummary:")
            print(f"  Total Nodes: {len(nodes)}")
            print(f"  Nodes with Questions: {nodes_with_questions}")
            print(f"  Total Questions (Linked to this graph): {total_questions}")
            
            # Global check
            print("\n--- Global Debug ---")
            global_count = await session.scalar(select(func.count(Question.id)))
            print(f"Total Questions in DB (All Graphs): {global_count}")
            
            if global_count > 0:
                # Group by graph_id
                stmt = select(Question.graph_id, func.count(Question.id)).group_by(Question.graph_id)
                results = await session.execute(stmt)
                for gid, count in results:
                    print(f"  Graph {gid}: {count} questions")
                    # Get graph details
                    from app.models.knowledge_graph import KnowledgeGraph
                    g_stmt = select(KnowledgeGraph).where(KnowledgeGraph.id == gid)
                    g_res = await session.execute(g_stmt)
                    g = g_res.scalar_one_or_none()
                    if g:
                        print(f"    -> Name: {g.name}, Slug: {g.slug}, Created: {g.created_at}")
                    else:
                        print(f"    -> Graph not found in knowledge_graphs table!")
            
            if total_questions == 0:
                print("\n❌ NO QUESTIONS FOUND FOR TARGET GRAPH! Linkage issue confirmed.")
            else:
                print("\n✅ Questions exist and are linked.")

    except Exception as e:
        print(f"❌ Verification failed: {e}")
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(verify_questions())
