"""
Entry point for running the MCP server as a module.

Usage:
    python -m app.mcp.server
"""

import asyncio

from app.mcp.server import main

if __name__ == "__main__":
    asyncio.run(main())
