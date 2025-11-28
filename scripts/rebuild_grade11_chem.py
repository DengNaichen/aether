#!/usr/bin/env python3
"""
Grade 11 Chemistry Graph Rebuild Script

This script:
1. Merges all chapter markdown files into one document
2. Deletes the existing Grade 11 Chemistry graph and ALL related data
3. Creates a new graph with is_template=True
4. Generates questions for all leaf nodes

Usage:
    python scripts/rebuild_grade11_chem.py

    # Dry run (don't make changes)
    python scripts/rebuild_grade11_chem.py --dry-run

    # Skip question generation
    python scripts/rebuild_grade11_chem.py --skip-questions

Environment:
    GOOGLE_API_KEY: Required for LLM API access
    DATABASE_URL: Required for PostgreSQL connection
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
    load_dotenv()

from sqlalchemy import select, delete

from app.core.database import db_manager
from app.models import (
    Base,
    User,
    KnowledgeGraph,
    KnowledgeNode,
    Prerequisite,
    Subtopic,
    Question,
    UserMastery,
    GraphEnrollment,
    SubmissionAnswer,
)
from app.crud import knowledge_graph as kg_crud
from app.schemas.knowledge_node import (
    GraphStructureImport,
    NodeImport,
    PrerequisiteImport,
    SubtopicImport,
)
from app.utils.slug import slugify
from app.services.generate_graph import (
    process_markdown,
    merge_graphs,
    PipelineConfig,
    MissingAPIKeyError,
    GraphStructureLLM,
)

# Configuration
GRAPH_NAME = "Grade 11 Chemistry"
GRAPH_SLUG = "grade-11-chemistry"
GRAPH_DESCRIPTION = "Complete Grade 11 Chemistry curriculum covering matter, elements, compounds, and chemical reactions."
MARKDOWN_DIR = project_root / "Resource" / "distilled_markdowns"
MERGED_OUTPUT = project_root / "Resource" / "grade11_chemistry_merged.md"
ADMIN_EMAIL = "admin@example.com"


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def merge_markdown_files(markdown_dir: Path, output_path: Path) -> Path:
    """
    Merge all chapter markdown files into a single document.

    Args:
        markdown_dir: Directory containing chapter*.md files
        output_path: Path to write merged output

    Returns:
        Path to merged file
    """
    chapter_files = sorted(markdown_dir.glob("chapter*.md"))

    if not chapter_files:
        raise FileNotFoundError(f"No chapter files found in {markdown_dir}")

    print(f"  Found {len(chapter_files)} chapter files:")
    for f in chapter_files:
        print(f"    - {f.name}")

    merged_content = []
    for chapter_file in chapter_files:
        content = chapter_file.read_text(encoding="utf-8")
        # Add chapter separator
        chapter_num = chapter_file.stem.replace("chapter", "")
        merged_content.append(f"\n\n# Chapter {chapter_num}\n\n")
        merged_content.append(content)

    full_content = "".join(merged_content)
    output_path.write_text(full_content, encoding="utf-8")

    print(f"  Merged content: {len(full_content):,} characters")
    print(f"  Output: {output_path}")

    return output_path


async def get_or_create_admin_user(session) -> User:
    """Get or create admin user for graph ownership"""
    stmt = select(User).where(User.email == ADMIN_EMAIL)
    result = await session.execute(stmt)
    admin_user = result.scalar_one_or_none()

    if admin_user:
        print(f"  Using admin user: {admin_user.email}")
        return admin_user

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


async def find_existing_graph(session, admin_user: User) -> KnowledgeGraph | None:
    """Find existing Grade 11 Chemistry graph"""
    # Try by slug first
    graph = await kg_crud.get_graph_by_owner_and_slug(session, admin_user.id, GRAPH_SLUG)
    if graph:
        return graph

    # Also check by name (case insensitive search)
    stmt = select(KnowledgeGraph).where(
        KnowledgeGraph.name.ilike(f"%grade%11%chem%")
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def delete_graph_and_related_data(session, graph: KnowledgeGraph):
    """
    Delete a knowledge graph and ALL related data.

    This includes:
    - SubmissionAnswers (references questions)
    - Questions
    - UserMastery
    - Prerequisites
    - Subtopics
    - KnowledgeNodes
    - GraphEnrollments
    - KnowledgeGraph itself
    """
    graph_id = graph.id
    print(f"  Deleting graph: {graph.name} ({graph_id})")

    # Get all node IDs for this graph (needed for submission_answers)
    node_ids_stmt = select(KnowledgeNode.id).where(KnowledgeNode.graph_id == graph_id)
    node_ids_result = await session.execute(node_ids_stmt)
    node_ids = [row[0] for row in node_ids_result.all()]

    # Get all question IDs for this graph (needed for submission_answers)
    question_ids_stmt = select(Question.id).where(Question.graph_id == graph_id)
    question_ids_result = await session.execute(question_ids_stmt)
    question_ids = [row[0] for row in question_ids_result.all()]

    # Delete in correct order to respect foreign key constraints

    # 1. Delete submission_answers that reference questions in this graph
    if question_ids:
        delete_submissions = delete(SubmissionAnswer).where(
            SubmissionAnswer.question_id.in_(question_ids)
        )
        result = await session.execute(delete_submissions)
        print(f"    Deleted {result.rowcount} submission answers")

    # 2. Delete questions
    delete_questions = delete(Question).where(Question.graph_id == graph_id)
    result = await session.execute(delete_questions)
    print(f"    Deleted {result.rowcount} questions")

    # 3. Delete user mastery
    delete_mastery = delete(UserMastery).where(UserMastery.graph_id == graph_id)
    result = await session.execute(delete_mastery)
    print(f"    Deleted {result.rowcount} user mastery records")

    # 4. Delete prerequisites
    delete_prereqs = delete(Prerequisite).where(Prerequisite.graph_id == graph_id)
    result = await session.execute(delete_prereqs)
    print(f"    Deleted {result.rowcount} prerequisites")

    # 5. Delete subtopics
    delete_subtopics = delete(Subtopic).where(Subtopic.graph_id == graph_id)
    result = await session.execute(delete_subtopics)
    print(f"    Deleted {result.rowcount} subtopics")

    # 6. Delete knowledge nodes
    delete_nodes = delete(KnowledgeNode).where(KnowledgeNode.graph_id == graph_id)
    result = await session.execute(delete_nodes)
    print(f"    Deleted {result.rowcount} knowledge nodes")

    # 7. Delete graph enrollments
    delete_enrollments = delete(GraphEnrollment).where(GraphEnrollment.graph_id == graph_id)
    result = await session.execute(delete_enrollments)
    print(f"    Deleted {result.rowcount} enrollments")

    # 8. Delete the graph itself
    delete_graph = delete(KnowledgeGraph).where(KnowledgeGraph.id == graph_id)
    await session.execute(delete_graph)
    print(f"    Deleted knowledge graph")

    await session.commit()
    print(f"  Graph deletion complete!")


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
        elif rel.label == "HAS_SUBTOPIC" and rel.child_id:
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
        description="Rebuild Grade 11 Chemistry knowledge graph",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--skip-questions",
        action="store_true",
        help="Skip question generation step"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-3-pro-preview",
        help="LLM model for graph extraction (default: gemini-3-pro-preview)"
    )
    parser.add_argument(
        "--questions-per-node",
        type=int,
        default=3,
        help="Number of questions to generate per leaf node (default: 3)"
    )

    args = parser.parse_args()

    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║   Grade 11 Chemistry Graph Rebuild                         ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
""")

    if args.dry_run:
        print("  *** DRY RUN MODE - No changes will be made ***\n")

    try:
        # Step 1: Merge markdown files
        print_section("Step 1: Merging Markdown Files")
        merged_file = merge_markdown_files(MARKDOWN_DIR, MERGED_OUTPUT)

        if args.dry_run:
            print("  [DRY RUN] Would create merged file")

        # Step 2: Extract knowledge graph from merged content
        print_section("Step 2: Extracting Knowledge Graph")
        print(f"  Model: {args.model}")

        config = PipelineConfig(model_name=args.model)

        # Process each chapter individually
        chapter_files = sorted(MARKDOWN_DIR.glob("chapter*.md"))
        extracted_graphs = []

        print(f"  Processing {len(chapter_files)} chapters...")
        
        for chapter_file in chapter_files:
            print(f"    Processing {chapter_file.name}...")
            chapter_graph = process_markdown(
                md_path=chapter_file,
                user_guidance="This is a Grade 11 Chemistry curriculum. Focus on testable concepts.",
                config=config,
            )
            
            if chapter_graph:
                extracted_graphs.append(chapter_graph)
                print(f"      Extracted: {len(chapter_graph.nodes)} nodes, {len(chapter_graph.relationships)} relationships")
            else:
                print(f"      Warning: Failed to extract graph from {chapter_file.name}")

        if not extracted_graphs:
            print("Error: Failed to extract knowledge graph from any chapter")
            sys.exit(1)

        # Merge graphs
        print(f"  Merging {len(extracted_graphs)} graphs...")
        extracted_graph = merge_graphs(extracted_graphs)

        print(f"  Total Extracted: {len(extracted_graph.nodes)} nodes, {len(extracted_graph.relationships)} relationships")

        prereq_count = sum(1 for r in extracted_graph.relationships if r.label == "IS_PREREQUISITE_FOR")
        subtopic_count = sum(1 for r in extracted_graph.relationships if r.label == "HAS_SUBTOPIC")
        print(f"    - Prerequisites: {prereq_count}")
        print(f"    - Subtopics: {subtopic_count}")

        if args.dry_run:
            print("\n  [DRY RUN] Extracted nodes preview:")
            for node in extracted_graph.nodes[:10]:
                print(f"    - {node.name}")
            if len(extracted_graph.nodes) > 10:
                print(f"    ... and {len(extracted_graph.nodes) - 10} more")
            print("\n  [DRY RUN] Exiting before database changes")
            return

        # Step 3: Connect to database and perform operations
        print_section("Step 3: Database Operations")
        await db_manager.initialize()
        await db_manager.create_all_tables(Base)

        async with db_manager.get_sql_session() as session:
            # Get admin user
            admin_user = await get_or_create_admin_user(session)

            # Find and delete existing graph
            print_section("Step 4: Deleting Existing Graph")
            existing_graph = await find_existing_graph(session, admin_user)

            if existing_graph:
                print(f"  Found existing graph: {existing_graph.name}")
                await delete_graph_and_related_data(session, existing_graph)
            else:
                print("  No existing Grade 11 Chemistry graph found")

            # Create new graph
            print_section("Step 5: Creating New Knowledge Graph")
            new_graph = await kg_crud.create_knowledge_graph(
                db_session=session,
                owner_id=admin_user.id,
                name=GRAPH_NAME,
                slug=GRAPH_SLUG,
                description=GRAPH_DESCRIPTION,
                is_public=True,
                is_template=True,  # Mark as template
            )
            print(f"  Created: {new_graph.name}")
            print(f"  ID: {new_graph.id}")
            print(f"  is_template: {new_graph.is_template}")

            # Import graph structure
            print_section("Step 6: Importing Graph Structure")
            import_data = convert_llm_output_to_import(extracted_graph)

            result = await kg_crud.import_graph_structure(
                db_session=session,
                graph_id=new_graph.id,
                import_data=import_data
            )

            print(f"  {result.message}")
            print(f"    Nodes created: {result.nodes_created}")
            print(f"    Prerequisites created: {result.prerequisites_created}")
            print(f"    Subtopics created: {result.subtopics_created}")

            graph_id = str(new_graph.id)

        # Step 7: Generate questions
        if not args.skip_questions:
            print_section("Step 7: Generating Questions")
            print(f"  Questions per node: {args.questions_per_node}")
            print(f"  Model: {args.model}")

            from app.services.generate_questions import generate_questions_for_graph, PipelineConfig as QuestionPipelineConfig
            
            q_config = QuestionPipelineConfig(model_name=args.model)

            question_result = await generate_questions_for_graph(
                graph_id=graph_id,
                questions_per_node=args.questions_per_node,
                only_nodes_without_questions=True,
                config=q_config,
            )

            print(f"  Nodes processed: {question_result['nodes_processed']}")
            print(f"  Questions generated: {question_result['questions_generated']}")
            print(f"  Questions saved: {question_result['questions_saved']}")

            if question_result["errors"]:
                print(f"  Errors: {len(question_result['errors'])}")
                for error in question_result["errors"][:5]:
                    print(f"    - {error}")
        else:
            print_section("Step 7: Skipping Question Generation")
            print("  (Use --skip-questions=false to generate questions)")

        # Done
        print_section("Complete!")
        print(f"""
Rebuild successful!

Graph Information:
  ID: {graph_id}
  Name: {GRAPH_NAME}
  is_template: True

Merged markdown saved to:
  {MERGED_OUTPUT}

Next steps:
  - View graph: GET /me/graphs/{graph_id}
  - Visualize: GET /graphs/{graph_id}/visualization
""")

    except MissingAPIKeyError as e:
        print(f"\nError: {e}")
        print("Please set GOOGLE_API_KEY environment variable")
        sys.exit(1)

    except Exception as e:
        print_section("Error")
        print(f"Rebuild failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
