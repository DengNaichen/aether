"""
MCP Tools - Functions that can be called by AI assistants.

Tools allow AI assistants to perform actions and query data.
"""

import logging
from typing import Any

from mcp import Tool
from mcp.types import TextContent

logger = logging.getLogger(__name__)


async def list_tools() -> list[Tool]:
    """
    List all available tools.

    Returns:
        List of Tool objects describing available functions.
    """
    return [
        Tool(
            name="echo",
            description="Echo back a message (useful for testing MCP connection)",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message to echo back",
                    }
                },
                "required": ["message"],
            },
        ),
        Tool(
            name="get_node_info",
            description="Get information about a knowledge node by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_name": {
                        "type": "string",
                        "description": "The name of the knowledge node to look up",
                    }
                },
                "required": ["node_name"],
            },
        ),
    ]


async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """
    Execute a tool call.

    Args:
        name: The name of the tool to call.
        arguments: The arguments to pass to the tool.

    Returns:
        List of TextContent objects with the tool's response.

    Raises:
        ValueError: If the tool name is not recognized.
    """
    logger.info(f"Calling tool: {name} with arguments: {arguments}")

    if name == "echo":
        return await _tool_echo(arguments)
    elif name == "get_node_info":
        return await _tool_get_node_info(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def _tool_echo(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Echo tool - simply returns the message back.

    This is useful for testing the MCP connection.
    """
    message = arguments.get("message", "")
    response = f"Echo: {message}"

    return [TextContent(type="text", text=response)]


async def _tool_get_node_info(arguments: dict[str, Any]) -> list[TextContent]:
    """
    Get information about a knowledge node.

    TODO: Integrate with actual database queries.
    """
    node_name = arguments.get("node_name", "")

    # Mock response for now
    response = f"""
Knowledge Node: {node_name}
Status: Mock Data (Database integration pending)

This tool will eventually query the Aether database to retrieve:
- Node description
- Prerequisites
- Dependent nodes
- Associated questions
- Learning statistics

For now, this is a placeholder response to test the MCP infrastructure.
""".strip()

    return [TextContent(type="text", text=response)]
