"""
MCP Resources - Data sources that can be read by AI assistants.

Resources are identified by URIs and provide read-only access to data.
"""

import logging

from mcp import Resource

logger = logging.getLogger(__name__)


async def list_resources() -> list[Resource]:
    """
    List all available resources.

    Returns:
        List of Resource objects describing available data sources.
    """
    return [
        Resource(
            uri="knowledge-graph://stats",
            name="Knowledge Graph Statistics",
            description="Get statistics about the knowledge graph (total nodes, edges, etc.)",
            mimeType="application/json",
        ),
        Resource(
            uri="aether://info",
            name="Aether System Info",
            description="General information about the Aether learning system",
            mimeType="text/plain",
        ),
    ]


async def read_resource(uri: str) -> str:
    """
    Read the content of a specific resource.

    Args:
        uri: The resource URI to read.

    Returns:
        The resource content as a string.

    Raises:
        ValueError: If the resource URI is not found.
    """
    logger.info(f"Reading resource: {uri}")

    if uri == "knowledge-graph://stats":
        # TODO: Replace with actual database query
        # For now, return mock data
        return _get_graph_stats()

    elif uri == "aether://info":
        return _get_system_info()

    else:
        raise ValueError(f"Unknown resource URI: {uri}")


def _get_graph_stats() -> str:
    """
    Get knowledge graph statistics.

    TODO: Integrate with actual database queries.
    """
    # Mock data for now
    stats = {
        "total_nodes": 0,
        "total_edges": 0,
        "total_graphs": 0,
        "status": "mock_data",
        "message": "Database integration pending",
    }

    import json

    return json.dumps(stats, indent=2)


def _get_system_info() -> str:
    """Get general system information."""
    info = """
Aether Learning System
======================

Aether is an adaptive learning backend built on:
- Knowledge graphs with prerequisite relationships
- FSRS (Free Spaced Repetition Scheduler) for mastery tracking
- Gemini-powered content ingestion and question generation

This MCP server provides tools and resources for AI-assisted learning.

Version: 0.1.0
Status: Development
"""
    return info.strip()
