"""
Setup demo data in Neo4j for visualization and exploration.

This script creates a complete knowledge graph with:
- 2 Courses (Physics G10, Chemistry G10)
- 15 Knowledge Nodes
- 20 Relationships
- 4 Sample Questions

The data will persist in Neo4j until you manually delete it.

Usage:
    python scripts/setup_demo_data.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
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


# Data paths
EXAMPLE_DATA_DIR = project_root / "example_data"
NODES_CSV = EXAMPLE_DATA_DIR / "nodes.csv"
RELATIONSHIPS_CSV = EXAMPLE_DATA_DIR / "relationships.csv"
QUESTIONS_CSV = EXAMPLE_DATA_DIR / "questions.csv"


async def create_courses(db_manager: DatabaseManager):
    """Create the required courses."""
    print("\n" + "=" * 80)
    print("📚 STEP 1: Creating Courses")
    print("=" * 80)

    courses_to_create = [
        ("g10_phys", "Grade 10 Physics"),
        ("g10_chem", "Grade 10 Chemistry"),
    ]

    async with db_manager.neo4j_scoped_connection():
        for course_id, course_name in courses_to_create:
            # Check if course already exists
            existing = await asyncio.to_thread(
                neo.Course.nodes.get_or_none,
                course_id=course_id
            )

            if existing:
                print(f"   ✅ Course already exists: {course_id} - {course_name}")
            else:
                course = neo.Course(
                    course_id=course_id,
                    course_name=course_name
                )
                await asyncio.to_thread(course.save)
                print(f"   ✅ Created course: {course_id} - {course_name}")


async def import_nodes(worker_ctx: WorkerContext):
    """Import knowledge nodes."""
    print("\n" + "=" * 80)
    print("📦 STEP 2: Importing Knowledge Nodes")
    print("=" * 80)

    # Import from CSV (handler will process the file)
    # We need to copy the file since handler deletes it
    import shutil
    from tempfile import NamedTemporaryFile

    temp_file = NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    temp_path = Path(temp_file.name)
    temp_file.close()
    shutil.copy(NODES_CSV, temp_path)

    payload = {
        "file_path": str(temp_path),
        "requested_by": "demo_setup@example.com"
    }

    result = await handle_bulk_import_nodes(payload, worker_ctx)

    print(f"\n📊 Import Summary:")
    print(f"   Total: {result['total_rows']}")
    print(f"   ✅ Successful: {result['successful']}")
    print(f"   ❌ Failed: {result['failed']}")

    if result['failed'] > 0:
        print(f"\n⚠️  Errors:")
        for error in result['errors']:
            print(f"      Row {error['row']}: {error['error']}")

    return result


async def import_relationships(worker_ctx: WorkerContext):
    """Import relationships between nodes."""
    print("\n" + "=" * 80)
    print("🔗 STEP 3: Importing Relationships")
    print("=" * 80)

    import shutil
    from tempfile import NamedTemporaryFile

    temp_file = NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    temp_path = Path(temp_file.name)
    temp_file.close()
    shutil.copy(RELATIONSHIPS_CSV, temp_path)

    payload = {
        "file_path": str(temp_path),
        "requested_by": "demo_setup@example.com"
    }

    result = await handle_bulk_import_relations(payload, worker_ctx)

    print(f"\n📊 Import Summary:")
    print(f"   Total: {result['total_rows']}")
    print(f"   ✅ Successful: {result['successful']}")
    print(f"   ❌ Failed: {result['failed']}")

    if result['failed'] > 0:
        print(f"\n⚠️  Errors:")
        for error in result['errors']:
            print(f"      Row {error['row']}: {error['error']}")

    return result


async def import_questions(worker_ctx: WorkerContext):
    """Import sample questions."""
    print("\n" + "=" * 80)
    print("❓ STEP 4: Importing Questions")
    print("=" * 80)

    import shutil
    from tempfile import NamedTemporaryFile

    temp_file = NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    temp_path = Path(temp_file.name)
    temp_file.close()
    shutil.copy(QUESTIONS_CSV, temp_path)

    payload = {
        "file_path": str(temp_path),
        "requested_by": "demo_setup@example.com"
    }

    result = await handle_bulk_import_question(payload, worker_ctx)

    print(f"\n📊 Import Summary:")
    print(f"   Total: {result['total_rows']}")
    print(f"   ✅ Successful: {result['successful']}")
    print(f"   ❌ Failed: {result['failed']}")

    if result['failed'] > 0:
        print(f"\n⚠️  Errors:")
        for error in result['errors']:
            print(f"      Row {error['row']}: {error['error']}")

    return result


async def verify_data(db_manager: DatabaseManager):
    """Verify the imported data."""
    print("\n" + "=" * 80)
    print("🔍 STEP 5: Verifying Data")
    print("=" * 80)

    async with db_manager.neo4j_scoped_connection():
        # Count courses
        courses = await asyncio.to_thread(
            lambda: list(neo.Course.nodes.all())
        )
        print(f"\n   📚 Courses: {len(courses)}")
        for course in courses:
            print(f"      - {course.course_id}: {course.course_name}")

        # Count nodes
        all_nodes = await asyncio.to_thread(
            lambda: list(neo.KnowledgeNode.nodes.all())
        )
        print(f"\n   📌 Knowledge Nodes: {len(all_nodes)}")

        # Group by course
        physics_nodes = [n for n in all_nodes if "phys" in n.node_id.lower()]
        chem_nodes = [n for n in all_nodes if "chem" in n.node_id.lower()]

        print(f"      🔬 Physics Nodes: {len(physics_nodes)}")
        for node in physics_nodes[:3]:
            print(f"         - {node.node_id}: {node.node_name}")
        if len(physics_nodes) > 3:
            print(f"         ... and {len(physics_nodes) - 3} more")

        print(f"      ⚗️  Chemistry Nodes: {len(chem_nodes)}")
        for node in chem_nodes[:3]:
            print(f"         - {node.node_id}: {node.node_name}")
        if len(chem_nodes) > 3:
            print(f"         ... and {len(chem_nodes) - 3} more")

        # Count questions
        questions = await asyncio.to_thread(
            lambda: list(neo.MultipleChoice.nodes.all())
        )
        print(f"\n   ❓ Questions: {len(questions)}")

        # Group by difficulty
        easy = [q for q in questions if q.difficulty == "easy"]
        medium = [q for q in questions if q.difficulty == "medium"]
        hard = [q for q in questions if q.difficulty == "hard"]

        print(f"      Easy: {len(easy)}")
        print(f"      Medium: {len(medium)}")
        print(f"      Hard: {len(hard)}")

        # Show sample relationships
        print(f"\n   🔗 Sample Relationships:")
        sample_node = all_nodes[0] if all_nodes else None
        if sample_node:
            prereqs = await asyncio.to_thread(
                lambda: list(sample_node.prerequisites.all())
            )
            if prereqs:
                print(f"      {sample_node.node_name} requires:")
                for prereq in prereqs:
                    print(f"         → {prereq.node_name}")

            subtopics = await asyncio.to_thread(
                lambda: list(sample_node.subtopic.all())
            )
            if subtopics:
                print(f"      {sample_node.node_name} contains:")
                for subtopic in subtopics:
                    print(f"         → {subtopic.node_name}")


async def print_cypher_queries():
    """Print useful Cypher queries for exploring the data."""
    print("\n" + "=" * 80)
    print("📝 USEFUL CYPHER QUERIES")
    print("=" * 80)

    queries = [
        ("View all courses",
         "MATCH (c:Course) RETURN c"),

        ("View all knowledge nodes",
         "MATCH (n:KnowledgeNode) RETURN n LIMIT 25"),

        ("View complete knowledge graph",
         "MATCH (n:KnowledgeNode)-[r]->(m) RETURN n, r, m"),

        ("View nodes with their prerequisites",
         "MATCH (n:KnowledgeNode)-[:HAS_PREREQUISITES]->(prereq:KnowledgeNode) RETURN n.node_name as Node, collect(prereq.node_name) as Prerequisites"),

        ("View all questions with their nodes",
         "MATCH (q:MultipleChoice)-[:TESTS]->(n:KnowledgeNode) RETURN q.question_id, q.text, q.difficulty, n.node_name"),

        ("View physics knowledge graph only",
         "MATCH (c:Course {course_id: 'g10_phys'})<-[:BELONGS_TO]-(n:KnowledgeNode)-[r]->(m:KnowledgeNode) RETURN c, n, r, m"),

        ("Count nodes by course",
         "MATCH (n:KnowledgeNode)-[:BELONGS_TO]->(c:Course) RETURN c.course_name, count(n) as NodeCount"),
    ]

    print("\nYou can run these queries in Neo4j Browser (http://localhost:7474):\n")
    for i, (description, query) in enumerate(queries, 1):
        print(f"{i}. {description}:")
        print(f"   {query}\n")


async def main():
    """Main setup function."""
    print("\n" + "=" * 80)
    print("🚀 SETTING UP DEMO DATA IN NEO4J")
    print("=" * 80)
    print(f"\nThis will create a complete knowledge graph in Neo4j")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Neo4j URI: {settings.NEO4J_URI}")
    print(f"\n⚠️  This data will PERSIST until you manually delete it.")
    print(f"   To clean up later, run: python scripts/cleanup_demo_data.py")

    # Verify CSV files exist
    if not NODES_CSV.exists():
        print(f"\n❌ Error: {NODES_CSV} not found!")
        return
    if not RELATIONSHIPS_CSV.exists():
        print(f"\n❌ Error: {RELATIONSHIPS_CSV} not found!")
        return
    if not QUESTIONS_CSV.exists():
        print(f"\n❌ Error: {QUESTIONS_CSV} not found!")
        return

    print(f"\n✅ All CSV files found in {EXAMPLE_DATA_DIR}")

    # Confirm
    response = input("\nContinue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Cancelled.")
        return

    # Initialize database manager
    db_manager = DatabaseManager(settings)

    try:
        # Create courses
        await create_courses(db_manager)

        # Create worker context
        worker_ctx = WorkerContext(db_mng=db_manager)

        # Import data
        nodes_result = await import_nodes(worker_ctx)
        relations_result = await import_relationships(worker_ctx)
        questions_result = await import_questions(worker_ctx)

        # Verify
        await verify_data(db_manager)

        # Print helpful queries
        await print_cypher_queries()

        # Success summary
        print("\n" + "=" * 80)
        print("✅ DEMO DATA SETUP COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print(f"\n📈 Summary:")
        print(f"   ✅ {nodes_result['successful']} Knowledge Nodes created")
        print(f"   ✅ {relations_result['successful']} Relationships created")
        print(f"   ✅ {questions_result['successful']} Questions created")
        print(f"\n🌐 Open Neo4j Browser: http://localhost:7474")
        print(f"   Username: neo4j")
        print(f"   Password: (your Neo4j password)")
        print(f"\n🔍 Try running the Cypher queries above to explore the data!")
        print(f"\n🗑️  When done, clean up with: python scripts/cleanup_demo_data.py")
        print("=" * 80 + "\n")

    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
