
import asyncio
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
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
from app.services.generate_questions import generate_questions_for_graph, PipelineConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GRAPH_ID = "c18d6d95-77ed-4b41-a833-dc5cddec74f4"

async def main():
    print(f"Generating questions for graph: {GRAPH_ID}")
    
    try:
        await db_manager.initialize()
        
        config = PipelineConfig(
            model_name="gemini-2.5-pro",
            temperature=0.7,
            max_retry_attempts=3
        )
        
        stats = await generate_questions_for_graph(
            graph_id=GRAPH_ID,
            questions_per_node=3,
            config=config,
            only_nodes_without_questions=True 
        )
        
        print("\nGeneration Stats:")
        print(f"  Nodes Processed: {stats['nodes_processed']}")
        print(f"  Nodes Skipped: {stats['nodes_skipped']}")
        print(f"  Questions Generated: {stats['questions_generated']}")
        print(f"  Questions Saved: {stats['questions_saved']}")
        
        if stats['errors']:
            print("\nErrors:")
            for err in stats['errors']:
                print(f"  - {err}")

    except Exception as e:
        print(f"❌ Script failed: {e}")
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
