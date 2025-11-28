#!/usr/bin/env python3
"""
Knowledge Graph Export Script

Exports a knowledge graph from the database to JSON format.

Usage:
    python scripts/export_graph.py --graph-id <uuid>
    python scripts/export_graph.py --graph-id <uuid> --output graph.json

Examples:
    # Export to stdout
    python scripts/export_graph.py --graph-id eaa00a93-ce66-4c6f-9dc1-9f9b08cbaf73

    # Export to file
    python scripts/export_graph.py --graph-id eaa00a93-ce66-4c6f-9dc1-9f9b08cbaf73 -o chemistry.json
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from uuid import UUID

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
env_file = project_root / ".env.local"
if env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv()


async def export_graph(graph_id: UUID, output_path: Path | None = None):
    """Export a knowledge graph to JSON format."""
    from sqlalchemy import select
    from app.core.database import db_manager
    from app.models import Base, KnowledgeGraph, KnowledgeNode, NodePrerequisite, NodeSubtopic

    await db_manager.initialize()

    try:
        async with db_manager.get_sql_session() as session:
            # Get graph info
            stmt = select(KnowledgeGraph).where(KnowledgeGraph.id == graph_id)
            result = await session.execute(stmt)
            graph = result.scalar_one_or_none()

            if not graph:
                print(f"Error: Graph not found with ID: {graph_id}", file=sys.stderr)
                sys.exit(1)

            # Get all nodes
            stmt = select(KnowledgeNode).where(KnowledgeNode.graph_id == graph_id)
            result = await session.execute(stmt)
            nodes = result.scalars().all()

            # Get all prerequisites
            node_ids = [n.id for n in nodes]
            stmt = select(NodePrerequisite).where(NodePrerequisite.from_node_id.in_(node_ids))
            result = await session.execute(stmt)
            prerequisites = result.scalars().all()

            # Get all subtopics
            stmt = select(NodeSubtopic).where(NodeSubtopic.parent_node_id.in_(node_ids))
            result = await session.execute(stmt)
            subtopics = result.scalars().all()

            # Build node lookup for names
            node_lookup = {n.id: n for n in nodes}

            # Build export structure
            export_data = {
                "graph": {
                    "id": str(graph.id),
                    "name": graph.name,
                    "slug": graph.slug,
                    "description": graph.description,
                    "is_public": graph.is_public,
                    "is_template": graph.is_template,
                },
                "nodes": [
                    {
                        "id": str(n.id),
                        "node_id_str": n.node_id_str,
                        "name": n.name,
                        "description": n.description,
                    }
                    for n in nodes
                ],
                "prerequisites": [
                    {
                        "from_node": node_lookup[p.from_node_id].name if p.from_node_id in node_lookup else str(p.from_node_id),
                        "to_node": node_lookup[p.to_node_id].name if p.to_node_id in node_lookup else str(p.to_node_id),
                        "weight": p.weight,
                    }
                    for p in prerequisites
                ],
                "subtopics": [
                    {
                        "parent_node": node_lookup[s.parent_node_id].name if s.parent_node_id in node_lookup else str(s.parent_node_id),
                        "child_node": node_lookup[s.child_node_id].name if s.child_node_id in node_lookup else str(s.child_node_id),
                        "weight": s.weight,
                    }
                    for s in subtopics
                ],
                "summary": {
                    "total_nodes": len(nodes),
                    "total_prerequisites": len(prerequisites),
                    "total_subtopics": len(subtopics),
                }
            }

            # Output
            json_output = json.dumps(export_data, indent=2, ensure_ascii=False)

            if output_path:
                output_path.write_text(json_output, encoding="utf-8")
                print(f"Exported to: {output_path}")
                print(f"  Nodes: {len(nodes)}")
                print(f"  Prerequisites: {len(prerequisites)}")
                print(f"  Subtopics: {len(subtopics)}")
            else:
                print(json_output)

    finally:
        await db_manager.close()


def main():
    parser = argparse.ArgumentParser(
        description="Export knowledge graph to JSON format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--graph-id",
        type=str,
        required=True,
        help="UUID of the graph to export"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file path (default: stdout)"
    )

    args = parser.parse_args()

    try:
        graph_id = UUID(args.graph_id)
    except ValueError:
        print(f"Error: Invalid UUID: {args.graph_id}", file=sys.stderr)
        sys.exit(1)

    asyncio.run(export_graph(graph_id, args.output))


if __name__ == "__main__":
    main()
