#!/usr/bin/env python3
"""
Setup Development Data for PostgreSQL-based Knowledge Graph System

This script loads development data using the new PostgreSQL architecture:
- Creates a KnowledgeGraph
- Creates KnowledgeNodes
- Creates Prerequisite and Subtopic relationships
- Creates Questions

Data source: CSV files in Resource/ directory

Usage:
    python scripts/setup_dev_data_pg.py
"""

import asyncio
import csv
import json
import sys
from pathlib import Path
from typing import Dict, Optional
from uuid import UUID

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import db_manager
from app.models import Base, User
from app.models.quiz import SubmissionAnswer  # Import for relationship resolution
from app.crud import knowledge_graph as kg_crud
from app.utils.slug import slugify

# Graph configuration
GRAPH_NAME = "Grade 11 Physics - Chapter 1: Kinematics"
GRAPH_DESCRIPTION = "Introduction to kinematics: displacement, velocity, and acceleration"
GRAPH_TAGS = ["physics", "grade11", "kinematics", "template"]
GRAPH_IS_PUBLIC = True
GRAPH_IS_TEMPLATE = True  # Mark as official template curriculum

# Admin user for setup (must exist in database)
ADMIN_EMAIL = "admin@example.com"

# Data files
RESOURCE_DIR = project_root / "Resource"
NODE_CSV = RESOURCE_DIR / "node.csv"
SUBTOPIC_CSV = RESOURCE_DIR / "has_subtopic.csv"
PREREQ_CSV = RESOURCE_DIR / "has_prerequisites.csv"
QUESTION_CSV = RESOURCE_DIR / "mcq.csv"


class SetupError(Exception):
    """Setup error"""
    pass


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


async def check_files_exist():
    """Check if all required data files exist"""
    print_section("Checking data files")

    files = [NODE_CSV, SUBTOPIC_CSV, PREREQ_CSV, QUESTION_CSV]
    missing = []

    for file_path in files:
        if file_path.exists():
            print(f"✅ {file_path.name}")
        else:
            print(f"❌ {file_path.name} - file not found")
            missing.append(file_path)

    if missing:
        raise SetupError(f"Missing required files: {[str(f) for f in missing]}")

    print("\nAll file checks passed!")


async def get_or_create_admin_user(session) -> User:
    """Get or create admin user for graph ownership"""
    print_section("Checking admin user")

    from sqlalchemy import select

    stmt = select(User).where(User.email == ADMIN_EMAIL)
    result = await session.execute(stmt)
    admin_user = result.scalar_one_or_none()

    if admin_user:
        print(f"✅ Found admin user: {admin_user.email} (ID: {admin_user.id})")
        return admin_user

    # Create admin user if doesn't exist
    print(f"Creating admin user: {ADMIN_EMAIL}")
    admin_user = User(
        email=ADMIN_EMAIL,
        name="Admin User",
        hashed_password="dummy_hash",  # TODO: Set proper password
        is_admin=True,
        is_active=True
    )
    session.add(admin_user)
    await session.commit()
    await session.refresh(admin_user)
    print(f"✅ Created admin user: {admin_user.email} (ID: {admin_user.id})")
    return admin_user


async def create_knowledge_graph(session, owner_id: UUID):
    """Create or get knowledge graph"""
    print_section("Creating Knowledge Graph")

    slug = slugify(GRAPH_NAME)

    # Check if graph already exists
    existing_graph = await kg_crud.get_graph_by_owner_and_slug(
        db_session=session,
        owner_id=owner_id,
        slug=slug
    )

    if existing_graph:
        print(f"ℹ️  Knowledge graph already exists:")
        print(f"   ID: {existing_graph.id}")
        print(f"   Name: {existing_graph.name}")
        print(f"   Slug: {existing_graph.slug}")
        return existing_graph

    # Create new graph
    graph = await kg_crud.create_knowledge_graph(
        db_session=session,
        owner_id=owner_id,
        name=GRAPH_NAME,
        slug=slug,
        description=GRAPH_DESCRIPTION,
        tags=GRAPH_TAGS,
        is_public=GRAPH_IS_PUBLIC,
        is_template=GRAPH_IS_TEMPLATE
    )

    print(f"✅ Successfully created knowledge graph:")
    print(f"   ID: {graph.id}")
    print(f"   Name: {graph.name}")
    print(f"   Slug: {graph.slug}")
    print(f"   Owner ID: {graph.owner_id}")
    print(f"   Is Template: {graph.is_template}")
    print(f"   Is Public: {graph.is_public}")

    return graph


async def import_knowledge_nodes(session, graph_id: UUID) -> Dict[str, UUID]:
    """Import knowledge nodes from CSV and return mapping of node_id_string -> UUID"""
    print_section("Importing knowledge nodes")

    node_id_map = {}  # Maps CSV node_id (string) -> PostgreSQL UUID
    successful = 0
    failed = 0
    errors = []

    with open(NODE_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        total = sum(1 for _ in open(NODE_CSV)) - 1  # Count rows minus header

        # Reset file pointer
        f.seek(0)
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader, start=1):
            try:
                csv_node_id = row['node_id:ID'].strip()
                node_name = row['node_name'].strip()
                description = row['description'].strip()

                # Try to find existing node by node_id_str (idempotency)
                existing_node = await kg_crud.get_node_by_str_id(
                    db_session=session,
                    graph_id=graph_id,
                    node_id_str=csv_node_id
                )

                if existing_node:
                    # Update existing node
                    existing_node.node_name = node_name
                    existing_node.description = description
                    await session.commit()
                    await session.refresh(existing_node)
                    node = existing_node
                else:
                    # Create new node
                    node = await kg_crud.create_knowledge_node(
                        db_session=session,
                        graph_id=graph_id,
                        node_name=node_name,
                        node_id_str=csv_node_id,  # Save CSV ID for traceability
                        description=description
                    )

                # Store mapping for relationship creation
                node_id_map[csv_node_id] = node.id

                successful += 1
                if idx % 10 == 0 or idx == total:
                    print(f"  Progress: {idx}/{total} ({successful} succeeded, {failed} failed)")

            except Exception as e:
                failed += 1
                errors.append({"node_id": row.get('node_id:ID', 'unknown'), "error": str(e)})

    print(f"\n✅ Knowledge nodes import completed:")
    print(f"   Total: {successful + failed}")
    print(f"   Succeeded: {successful}")
    print(f"   Failed: {failed}")

    if errors:
        print(f"\n❌ Error details:")
        for err in errors[:5]:  # Show first 5 errors
            print(f"   - {err['node_id']}: {err['error']}")

    return node_id_map


async def import_subtopics(session, graph_id: UUID, node_id_map: Dict[str, UUID]):
    """Import subtopic relationships"""
    print_section("Importing subtopic relationships")

    successful = 0
    failed = 0
    errors = []

    with open(SUBTOPIC_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        total = sum(1 for _ in open(SUBTOPIC_CSV)) - 1

        f.seek(0)
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader, start=1):
            try:
                parent_node_str = row[':START_ID(KnowledgeNode)'].strip()
                child_node_str = row[':END_ID(KnowledgeNode)'].strip()
                weight = float(row['weight'].strip())

                # Map CSV IDs to PostgreSQL UUIDs
                parent_node_id = node_id_map.get(parent_node_str)
                child_node_id = node_id_map.get(child_node_str)

                if not parent_node_id or not child_node_id:
                    raise ValueError(
                        f"Node not found: parent={parent_node_str}, child={child_node_str}"
                    )

                # Create subtopic relationship
                await kg_crud.create_subtopic(
                    db_session=session,
                    graph_id=graph_id,
                    parent_node_id=parent_node_id,
                    child_node_id=child_node_id,
                    weight=weight
                )

                successful += 1
                if idx % 10 == 0 or idx == total:
                    print(f"  Progress: {idx}/{total} ({successful} succeeded, {failed} failed)")

            except Exception as e:
                failed += 1
                errors.append({
                    "parent": row.get(':START_ID(KnowledgeNode)', 'unknown'),
                    "child": row.get(':END_ID(KnowledgeNode)', 'unknown'),
                    "error": str(e)
                })

    print(f"\n✅ Subtopic relationships import completed:")
    print(f"   Total: {successful + failed}")
    print(f"   Succeeded: {successful}")
    print(f"   Failed: {failed}")

    if errors:
        print(f"\n❌ Error details:")
        for err in errors[:5]:
            print(f"   - {err['parent']} -> {err['child']}: {err['error']}")


async def import_prerequisites(session, graph_id: UUID, node_id_map: Dict[str, UUID]):
    """Import prerequisite relationships"""
    print_section("Importing prerequisite relationships")

    successful = 0
    failed = 0
    errors = []

    with open(PREREQ_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        total = sum(1 for _ in open(PREREQ_CSV)) - 1

        f.seek(0)
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader, start=1):
            try:
                from_node_str = row[':START_ID(KnowledgeNode)'].strip()
                to_node_str = row[':END_ID(KnowledgeNode)'].strip()
                # weight = float(row.get('weight', '1.0').strip())  # Default to 1.0

                # Map CSV IDs to PostgreSQL UUIDs
                from_node_id = node_id_map.get(from_node_str)
                to_node_id = node_id_map.get(to_node_str)

                if not from_node_id or not to_node_id:
                    raise ValueError(
                        f"Node not found: from={from_node_str}, to={to_node_str}"
                    )

                # Create prerequisite relationship
                await kg_crud.create_prerequisite(
                    db_session=session,
                    graph_id=graph_id,
                    from_node_id=from_node_id,
                    to_node_id=to_node_id,
                    weight=1.0  # Default weight
                )

                successful += 1
                if idx % 10 == 0 or idx == total:
                    print(f"  Progress: {idx}/{total} ({successful} succeeded, {failed} failed)")

            except Exception as e:
                failed += 1
                errors.append({
                    "from": row.get(':START_ID(KnowledgeNode)', 'unknown'),
                    "to": row.get(':END_ID(KnowledgeNode)', 'unknown'),
                    "error": str(e)
                })

    print(f"\n✅ Prerequisite relationships import completed:")
    print(f"   Total: {successful + failed}")
    print(f"   Succeeded: {successful}")
    print(f"   Failed: {failed}")

    if errors:
        print(f"\n❌ Error details:")
        for err in errors[:5]:
            print(f"   - {err['from']} -> {err['to']}: {err['error']}")


async def import_questions(session, graph_id: UUID, node_id_map: Dict[str, UUID]):
    """Import multiple choice questions"""
    print_section("Importing multiple choice questions")

    successful = 0
    failed = 0
    skipped = 0
    errors = []

    with open(QUESTION_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        total = sum(1 for _ in open(QUESTION_CSV)) - 1

        f.seek(0)
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader, start=1):
            try:
                # question_id_str = row['question_id'].strip()  # We'll generate new UUIDs
                knowledge_node_str = row['knowledge_node_id'].strip()
                text = row['text'].strip()
                options_str = row['options'].strip()
                correct_answer = int(row['correct_answer'])
                difficulty = row['difficulty'].strip().lower()
                p_s = float(row.get('p_s', '0.1').strip())

                # Skip SAMPLE questions in production
                # Uncomment for production:
                # if text.startswith('SAMPLE'):
                #     skipped += 1
                #     continue

                # Parse options
                try:
                    options = json.loads(options_str)
                except json.JSONDecodeError:
                    raise ValueError(f"Invalid JSON format: {options_str}")

                # Get node UUID from mapping
                node_id = node_id_map.get(knowledge_node_str)
                if not node_id:
                    raise ValueError(f"Knowledge node {knowledge_node_str} not found in mapping")

                # Calculate p_g based on number of options
                p_g = 1.0 / len(options) if options else 0.25

                # Create question details (JSONB field)
                details = {
                    "question_type": "multiple_choice",
                    "options": options,
                    "correct_answer": correct_answer,
                    "p_g": p_g,
                    "p_s": p_s
                }

                # Create question
                await kg_crud.create_question(
                    db_session=session,
                    graph_id=graph_id,
                    node_id=node_id,
                    question_type="multiple_choice",
                    text=text,
                    details=details,
                    difficulty=difficulty
                )

                successful += 1
                if idx % 20 == 0 or idx == total:
                    print(f"  Progress: {idx}/{total} ({successful} succeeded, {skipped} skipped, {failed} failed)")

            except Exception as e:
                failed += 1
                errors.append({
                    "question_id": row.get('question_id', 'unknown'),
                    "error": str(e)
                })

    print(f"\n✅ Multiple choice questions import completed:")
    print(f"   Total: {successful + skipped + failed}")
    print(f"   Succeeded: {successful}")
    print(f"   Skipped (SAMPLE): {skipped}")
    print(f"   Failed: {failed}")

    if errors:
        print(f"\n❌ Error details:")
        for err in errors[:5]:
            print(f"   - {err['question_id']}: {err['error']}")


async def verify_data(session, graph_id: UUID):
    """Verify imported data"""
    print_section("Verifying data")

    # Count nodes
    nodes = await kg_crud.get_nodes_by_graph(session, graph_id)
    node_count = len(nodes)

    # Count questions
    questions = await kg_crud.get_questions_by_graph(session, graph_id)
    question_count = len(questions)

    # Count subtopics
    subtopics = await kg_crud.get_subtopics_by_graph(session, graph_id)
    subtopic_count = len(subtopics)

    # Count prerequisites
    prerequisites = await kg_crud.get_prerequisites_by_graph(session, graph_id)
    prereq_count = len(prerequisites)

    print(f"✅ Data verification:")
    print(f"   Graph ID: {graph_id}")
    print(f"   Knowledge nodes: {node_count}")
    print(f"   Questions: {question_count}")
    print(f"   Subtopic relationships: {subtopic_count}")
    print(f"   Prerequisite relationships: {prereq_count}")


async def main():
    """Main function"""
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║   PostgreSQL Knowledge Graph Data Loader                  ║
║                                                            ║
║   Graph: Grade 11 Physics - Chapter 1: Kinematics         ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
""")

    try:
        # Step 0: Initialize database and create tables
        await db_manager.initialize()
        await db_manager.create_all_tables(Base)
        print("✅ Database initialized and tables created")

        # Step 1: Check files
        await check_files_exist()

        # Step 2: Create/get admin user and knowledge graph
        async with db_manager.get_sql_session() as session:
            # Get admin user
            admin_user = await get_or_create_admin_user(session)

            # Create knowledge graph
            graph = await create_knowledge_graph(session, admin_user.id)
            graph_id = graph.id

            # Step 3: Import knowledge nodes
            node_id_map = await import_knowledge_nodes(session, graph_id)

            # Step 4: Import subtopic relationships
            await import_subtopics(session, graph_id, node_id_map)

            # Step 5: Import prerequisite relationships
            await import_prerequisites(session, graph_id, node_id_map)

            # Step 6: Import questions
            await import_questions(session, graph_id, node_id_map)

            # Step 7: Verify data
            await verify_data(session, graph_id)

        print_section("Completed")
        print(f"""
✅ PostgreSQL knowledge graph data loading completed!

Graph Information:
- Graph ID: {graph_id}
- Graph Name: {GRAPH_NAME}
- Owner: {ADMIN_EMAIL}

Data persistence notes:
- PostgreSQL data is stored in Docker volume 'postgres_data'
- Data will persist unless you run 'docker-compose down -v'

Usage tips:
- View graph: Use API endpoints at /me/graphs
- Practice mode: Use POST /answer endpoint
- Clean data: Delete graph via API or database

Start practicing! 🚀
""")

    except Exception as e:
        print_section("Error")
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
