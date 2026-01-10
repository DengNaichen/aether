"""
MCP Server for Aether Learning System.

This server exposes Aether's knowledge graph and learning features
via the Model Context Protocol (MCP).
"""

import asyncio
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server

from app.mcp.config import config
from app.mcp.resources import list_resources, read_resource
from app.mcp.tools import call_tool, list_tools

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def create_server() -> Server:
    """
    Create and configure the MCP server.

    Returns:
        Configured Server instance.
    """
    server = Server(config.server_name)

    logger.info(
        f"Initializing MCP server: {config.server_name} v{config.server_version}"
    )

    # Register resource handlers
    @server.list_resources()
    async def handle_list_resources():
        """Handle resource listing requests."""
        logger.debug("Listing resources")
        return await list_resources()

    @server.read_resource()
    async def handle_read_resource(uri: str):
        """Handle resource read requests."""
        logger.debug(f"Reading resource: {uri}")
        content = await read_resource(uri)
        return content

    # Register tool handlers
    @server.list_tools()
    async def handle_list_tools():
        """Handle tool listing requests."""
        logger.debug("Listing tools")
        return await list_tools()

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict):
        """Handle tool call requests."""
        logger.debug(f"Calling tool: {name}")
        return await call_tool(name, arguments)

    logger.info("MCP server initialized successfully")
    return server


async def main():
    """
    Main entry point for the MCP server.

    Runs the server using stdio transport (for Claude Desktop integration).
    """
    logger.info("Starting Aether MCP server...")

    server = create_server()

    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP server running on stdio")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
