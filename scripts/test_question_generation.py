
import asyncio
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from uuid import UUID
from sqlalchemy import select

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
from app.services.generate_questions import generate_questions_for_node, PipelineConfig, convert_to_question_create
from app.crud.knowledge_graph import get_leaf_nodes_by_graph, bulk_create_questions
from app.models.knowledge_node import KnowledgeNode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GRAPH_ID = "c18d6d95-77ed-4b41-a833-dc5cddec74f4"
TEST_NODE_COUNT = 2

async def main():
    print(f"Testing question generation for {TEST_NODE_COUNT} nodes")
    print(f"Graph ID: {GRAPH_ID}")
    print(f"Model: gemini-2.5-flash\n")
    
    try:
        await db_manager.initialize()
        
        config = PipelineConfig(
            model_name="gemini-2.5-flash",
            temperature=0.7,
            max_retry_attempts=3
        )
        
        async with db_manager.get_sql_session() as session:
            # Get first 2 leaf nodes
            graph_uuid = UUID(GRAPH_ID)
            leaf_nodes = await get_leaf_nodes_by_graph(session, graph_uuid)
            
            print(f"Found {len(leaf_nodes)} total leaf nodes")
            test_nodes = leaf_nodes[:TEST_NODE_COUNT]
            print(f"Testing with first {len(test_nodes)} nodes:\n")
            
            all_questions_data = []
            
            for i, node in enumerate(test_nodes, 1):
                print(f"[{i}/{len(test_nodes)}] Node: {node.node_name}")
                print(f"  ID: {node.id}")
                print(f"  Description: {node.description[:100]}...")
                
                try:
                    result = generate_questions_for_node(
                        node_name=node.node_name,
                        node_description=node.description,
                        num_questions=3,
                        question_types=["multiple_choice"],  # Only MCQ
                        config=config,
                    )
                    
                    if result and result.questions:
                        print(f"  ✅ Generated {len(result.questions)} questions")
                        
                        # Convert to database format
                        for q in result.questions:
                            q_data = convert_to_question_create(q, str(node.id))
                            all_questions_data.append(q_data)
                            print(f"    - {q.question_type} ({q.difficulty}): {q.text[:60]}...")
                    else:
                        print(f"  ❌ Failed to generate questions")
                        
                except Exception as e:
                    print(f"  ❌ Error: {e}")
                
                print()
            
            # Save to database
            if all_questions_data:
                print(f"\n{'='*60}")
                print(f"Saving {len(all_questions_data)} questions to database...")
                try:
                    saved_count = await bulk_create_questions(
                        session, graph_uuid, all_questions_data
                    )
                    print(f"✅ Successfully saved {saved_count} questions!")
                except Exception as e:
                    print(f"❌ Database save error: {e}")
            else:
                print("\n❌ No questions to save")

    except Exception as e:
        print(f"\n❌ Script failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
