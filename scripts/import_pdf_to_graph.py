#!/usr/bin/env python3
"""
Knowledge Graph Import Script

This script extracts a knowledge graph from markdown files using LLM
and imports it into the PostgreSQL database.

Usage:
    python scripts/import_pdf_to_graph.py --name "Graph Name" --files file1.md file2.md

Examples:
    # Create new graph from markdown files
    python scripts/import_pdf_to_graph.py --name "Grade 11 Chemistry" \
        --files Resource/distilled_markdowns/*.md

    # Import into existing graph
    python scripts/import_pdf_to_graph.py --graph-id <uuid> --files chapter1.md

    # With custom guidance for LLM
    python scripts/import_pdf_to_graph.py --name "Calculus" \
        --guidance "Focus on mathematical theorems and proofs" \
        --files textbook.md

Environment:
    GOOGLE_API_KEY: Required for LLM API access
"""

import argparse
import asyncio
import sys
from pathlib import Path
from uuid import UUID

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env.local
from dotenv import load_dotenv
env_file = project_root / ".env.local"
if env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv()  # Try default .env

from app.core.database import db_manager
from app.models import Base, User
from app.crud import knowledge_graph as kg_crud
from app.schemas.knowledge_node import (
    GraphStructureImport,
    NodeImport,
    PrerequisiteImport,
    SubtopicImport,
)
from app.utils.slug import slugify

# Import the markdown processing pipeline
from app.services.generate_graph import (
    process_markdown,
    merge_graphs,
    PipelineConfig,
    MissingAPIKeyError,
    GraphStructureLLM,
)


# Default admin user
ADMIN_EMAIL = "admin@example.com"


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_progress(current: int, total: int, message: str):
    """Progress callback for PDF processing"""
    bar_length = 40
    if total > 0:
        progress = current / total
        filled = int(bar_length * progress)
        bar = "=" * filled + "-" * (bar_length - filled)
        print(f"\r  [{bar}] {current}/{total} - {message}", end="", flush=True)
    else:
        print(f"  {message}")


async def get_or_create_admin_user(session) -> User:
    """Get or create admin user for graph ownership"""
    from sqlalchemy import select

    stmt = select(User).where(User.email == ADMIN_EMAIL)
    result = await session.execute(stmt)
    admin_user = result.scalar_one_or_none()

    if admin_user:
        print(f"  Using admin user: {admin_user.email}")
        return admin_user

    # Create admin user if doesn't exist
    print(f"  Creating admin user: {ADMIN_EMAIL}")
    admin_user = User(
        email=ADMIN_EMAIL,
        name="Admin User",
        hashed_password="dummy_hash",
        is_admin=True,
        is_active=True
    )
    session.add(admin_user)
    await session.commit()
    await session.refresh(admin_user)
    return admin_user


def convert_llm_output_to_import(graph: GraphStructureLLM) -> GraphStructureImport:
    """Convert LLM output format to database import format"""
    nodes = [
        NodeImport(
            node_id_str=node.id,
            node_name=node.name,
            description=node.description
        )
        for node in graph.nodes
    ]

    prerequisites = []
    subtopics = []

    for rel in graph.relationships:
        if rel.label == "IS_PREREQUISITE_FOR":
            prerequisites.append(PrerequisiteImport(
                from_node_id_str=rel.source_id,
                to_node_id_str=rel.target_id,
                weight=rel.weight
            ))
        elif rel.label == "HAS_SUBTOPIC":
            subtopics.append(SubtopicImport(
                parent_node_id_str=rel.parent_id,
                child_node_id_str=rel.child_id,
                weight=rel.weight
            ))

    return GraphStructureImport(
        nodes=nodes,
        prerequisites=prerequisites,
        subtopics=subtopics
    )


async def main():
    parser = argparse.ArgumentParser(
        description="Extract knowledge graph from markdown files and import to database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--files",
        type=Path,
        nargs="+",
        required=True,
        help="Path(s) to markdown file(s) to process"
    )
    parser.add_argument(
        "--name",
        type=str,
        help="Name for new knowledge graph (required if --graph-id not provided)"
    )
    parser.add_argument(
        "--graph-id",
        type=str,
        help="UUID of existing graph to import into"
    )
    parser.add_argument(
        "--description",
        type=str,
        default="",
        help="Description for new knowledge graph"
    )
    parser.add_argument(
        "--guidance",
        type=str,
        default="Focus on concepts that can be tested with quiz questions.",
        help="Additional guidance for LLM extraction"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-2.5-flash",
        help="LLM model to use (default: gemini-2.5-flash)"
    )
    parser.add_argument(
        "--template",
        action="store_true",
        help="Mark graph as template"
    )
    parser.add_argument(
        "--public",
        action="store_true",
        help="Mark graph as public"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract graph but don't save to database"
    )

    args = parser.parse_args()

    # Validate files exist
    valid_files = []
    for f in args.files:
        if f.exists():
            valid_files.append(f)
        else:
            print(f"Warning: File not found: {f}")

    if not valid_files:
        print("Error: No valid files to process")
        sys.exit(1)

    if not args.graph_id and not args.name:
        print("Error: Either --name (for new graph) or --graph-id (for existing graph) is required")
        sys.exit(1)

    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║   Markdown to Knowledge Graph Importer                    ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
""")

    try:
        # Step 1: Extract graph from markdown files
        print_section("Extracting Knowledge Graph from Markdown")
        print(f"  Files: {len(valid_files)}")
        for f in valid_files:
            print(f"    - {f}")
        print(f"  Model: {args.model}")
        if args.guidance:
            print(f"  Guidance: {args.guidance[:50]}...")
        print()

        config = PipelineConfig(model_name=args.model)

        # Process each file and merge results
        all_graphs = []
        for i, md_file in enumerate(valid_files):
            print(f"  [{i+1}/{len(valid_files)}] Processing {md_file.name}...")
            graph = process_markdown(
                md_path=md_file,
                user_guidance=args.guidance,
                config=config,
            )
            if graph:
                print(f"      Extracted: {len(graph.nodes)} nodes, {len(graph.relationships)} relationships")
                all_graphs.append(graph)
            else:
                print(f"      Failed to extract")

        if not all_graphs:
            print("\nError: Failed to extract knowledge graph from any file")
            sys.exit(1)

        # Merge all graphs
        extracted_graph = merge_graphs(all_graphs)

        print(f"\n  Extraction complete (merged):")
        print(f"    Nodes: {len(extracted_graph.nodes)}")
        print(f"    Relationships: {len(extracted_graph.relationships)}")

        # Count relationship types
        prereq_count = sum(1 for r in extracted_graph.relationships if r.label == "IS_PREREQUISITE_FOR")
        subtopic_count = sum(1 for r in extracted_graph.relationships if r.label == "HAS_SUBTOPIC")
        print(f"      - Prerequisites: {prereq_count}")
        print(f"      - Subtopics: {subtopic_count}")

        if args.dry_run:
            print_section("Dry Run - Skipping Database Import")
            print("  Extracted nodes:")
            for node in extracted_graph.nodes[:10]:
                print(f"    - {node.name}: {node.description[:50]}...")
            if len(extracted_graph.nodes) > 10:
                print(f"    ... and {len(extracted_graph.nodes) - 10} more")
            return

        # Step 2: Initialize database
        print_section("Connecting to Database")
        await db_manager.initialize()
        await db_manager.create_all_tables(Base)

        # Step 3: Get or create graph
        async with db_manager.get_sql_session() as session:
            if args.graph_id:
                # Use existing graph
                graph_id = UUID(args.graph_id)
                graph = await kg_crud.get_graph_by_id(session, graph_id)
                if not graph:
                    print(f"Error: Graph not found with ID: {args.graph_id}")
                    sys.exit(1)
                print(f"  Using existing graph: {graph.name} ({graph_id})")
            else:
                # Create new graph
                print_section("Creating Knowledge Graph")
                admin_user = await get_or_create_admin_user(session)

                slug = slugify(args.name)
                existing = await kg_crud.get_graph_by_owner_and_slug(
                    session, admin_user.id, slug
                )

                if existing:
                    print(f"  Graph already exists: {existing.name}")
                    graph = existing
                else:
                    graph = await kg_crud.create_knowledge_graph(
                        db_session=session,
                        owner_id=admin_user.id,
                        name=args.name,
                        slug=slug,
                        description=args.description,
                        is_public=args.public,
                        is_template=args.template
                    )
                    print(f"  Created graph: {graph.name}")

                graph_id = graph.id
                print(f"  Graph ID: {graph_id}")

            # Step 4: Convert and import
            print_section("Importing to Database")
            import_data = convert_llm_output_to_import(extracted_graph)

            result = await kg_crud.import_graph_structure(
                db_session=session,
                graph_id=graph_id,
                import_data=import_data
            )

            print(f"  {result.message}")
            print(f"    Nodes created: {result.nodes_created}")
            print(f"    Nodes skipped: {result.nodes_skipped}")
            print(f"    Prerequisites created: {result.prerequisites_created}")
            print(f"    Prerequisites skipped: {result.prerequisites_skipped}")
            print(f"    Subtopics created: {result.subtopics_created}")
            print(f"    Subtopics skipped: {result.subtopics_skipped}")

        # Done
        print_section("Completed")
        print(f"""
Import successful!

Graph Information:
  ID: {graph_id}
  Name: {graph.name}

Next steps:
  - View graph: GET /me/graphs/{graph_id}
  - Visualize: GET /graphs/{graph_id}/visualization
  - Add questions to nodes for practice mode
""")

    except MissingAPIKeyError as e:
        print(f"\nError: {e}")
        print("Please set GOOGLE_API_KEY environment variable")
        sys.exit(1)

    except Exception as e:
        print_section("Error")
        print(f"Import failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
