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
    print("="*60)
    print("Grade 11 Chemistry - MCQ Question Generation")
    print("="*60)
    print(f"Graph ID: {GRAPH_ID}")
    print(f"Model: gemini-2.5-flash")
    print(f"Question Type: Multiple Choice Only")
    print(f"Questions per Node: 3")
    print("="*60)
    print()
    
    try:
        await db_manager.initialize()
        
        config = PipelineConfig(
            model_name="gemini-2.5-flash",
            temperature=0.7,
            max_retry_attempts=3
        )
        
        stats = await generate_questions_for_graph(
            graph_id=GRAPH_ID,
            questions_per_node=3,
            question_types=["multiple_choice"],  # Only MCQ
            config=config,
            only_nodes_without_questions=True  # Skip nodes that already have questions
        )
        
        print("\n" + "="*60)
        print("Generation Complete!")
        print("="*60)
        print(f"Nodes Processed: {stats['nodes_processed']}")
        print(f"Nodes Skipped: {stats['nodes_skipped']}")
        print(f"Questions Generated: {stats['questions_generated']}")
        print(f"Questions Saved: {stats['questions_saved']}")
        
        if stats['errors']:
            print(f"\nErrors ({len(stats['errors'])}):")
            for err in stats['errors'][:10]:  # Show first 10 errors
                print(f"  - {err}")
            if len(stats['errors']) > 10:
                print(f"  ... and {len(stats['errors']) - 10} more errors")
        
        print("="*60)

    except Exception as e:
        print(f"\n❌ Script failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
