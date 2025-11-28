#!/usr/bin/env python3
"""
Script to generate questions for all leaf nodes in a knowledge graph.

Usage:
    # Generate 3 questions per node (default)
    python scripts/generate_questions_for_graph.py <graph_id>

    # Generate 5 questions per node
    python scripts/generate_questions_for_graph.py <graph_id> --questions-per-node 5

    # Specify difficulty distribution
    python scripts/generate_questions_for_graph.py <graph_id> --easy 2 --medium 2 --hard 1

    # Generate for ALL leaf nodes (including those with existing questions)
    python scripts/generate_questions_for_graph.py <graph_id> --regenerate

    # Add custom guidance
    python scripts/generate_questions_for_graph.py <graph_id> --guidance "Focus on calculation problems"

Environment:
    GOOGLE_API_KEY: Required. Your Google Gemini API key.
    DATABASE_URL: Required. PostgreSQL connection string.

Example:
    export GOOGLE_API_KEY="your-api-key"
    python scripts/generate_questions_for_graph.py 550e8400-e29b-41d4-a716-446655440000
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def main():
    parser = argparse.ArgumentParser(
        description="Generate questions for knowledge graph leaf nodes"
    )
    parser.add_argument(
        "graph_id",
        help="UUID of the knowledge graph"
    )
    parser.add_argument(
        "--questions-per-node", "-n",
        type=int,
        default=3,
        help="Number of questions to generate per node (default: 3)"
    )
    parser.add_argument(
        "--easy",
        type=int,
        default=None,
        help="Number of easy questions"
    )
    parser.add_argument(
        "--medium",
        type=int,
        default=None,
        help="Number of medium questions"
    )
    parser.add_argument(
        "--hard",
        type=int,
        default=None,
        help="Number of hard questions"
    )
    parser.add_argument(
        "--types",
        nargs="+",
        choices=["multiple_choice", "fill_blank", "short_answer"],
        help="Preferred question types"
    )
    parser.add_argument(
        "--guidance",
        type=str,
        default="",
        help="Additional instructions for the LLM"
    )
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Generate questions for ALL leaf nodes, even those with existing questions"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show what would be done, don't actually generate"
    )

    args = parser.parse_args()

    # Build difficulty distribution if specified
    difficulty_distribution = None
    if args.easy is not None or args.medium is not None or args.hard is not None:
        difficulty_distribution = {}
        if args.easy:
            difficulty_distribution["easy"] = args.easy
        if args.medium:
            difficulty_distribution["medium"] = args.medium
        if args.hard:
            difficulty_distribution["hard"] = args.hard

    print(f"Graph ID: {args.graph_id}")
    print(f"Questions per node: {args.questions_per_node}")
    if difficulty_distribution:
        print(f"Difficulty distribution: {difficulty_distribution}")
    if args.types:
        print(f"Question types: {args.types}")
    if args.guidance:
        print(f"Custom guidance: {args.guidance}")
    print(f"Only nodes without questions: {not args.regenerate}")
    print()

    if args.dry_run:
        # Just show leaf nodes that would be processed
        from uuid import UUID

        from app.core.database import db_manager
        from app.crud.knowledge_graph import (
            get_leaf_nodes_by_graph,
            get_leaf_nodes_without_questions,
        )

        graph_uuid = UUID(args.graph_id)

        async with db_manager.get_sql_session() as db_session:
            if args.regenerate:
                nodes = await get_leaf_nodes_by_graph(db_session, graph_uuid)
            else:
                nodes = await get_leaf_nodes_without_questions(db_session, graph_uuid)

        print(f"Found {len(nodes)} leaf nodes to process:")
        for i, node in enumerate(nodes, 1):
            desc_preview = (node.description or "")[:50] + "..." if node.description and len(node.description) > 50 else (node.description or "No description")
            print(f"  {i}. {node.node_name}: {desc_preview}")

        print()
        print("(Dry run - no questions generated)")
        return

    # Run the generation
    from app.services.generate_questions import generate_questions_for_graph

    result = await generate_questions_for_graph(
        graph_id=args.graph_id,
        questions_per_node=args.questions_per_node,
        difficulty_distribution=difficulty_distribution,
        question_types=args.types,
        user_guidance=args.guidance,
        only_nodes_without_questions=not args.regenerate,
    )

    print()
    print("=" * 50)
    print("Generation Complete!")
    print("=" * 50)
    print(f"Nodes processed: {result['nodes_processed']}")
    print(f"Nodes skipped: {result['nodes_skipped']}")
    print(f"Questions generated: {result['questions_generated']}")
    print(f"Questions saved to DB: {result['questions_saved']}")

    if result["errors"]:
        print()
        print("Errors encountered:")
        for error in result["errors"]:
            print(f"  - {error}")


if __name__ == "__main__":
    asyncio.run(main())
