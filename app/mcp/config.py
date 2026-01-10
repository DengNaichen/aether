"""
Configuration for the MCP server.
"""

import os
from dataclasses import dataclass


@dataclass
class MCPConfig:
    """Configuration for the MCP server."""

    # Server metadata
    server_name: str = "aether-learning"
    server_version: str = "0.1.0"

    # Database configuration (reuse from existing app config)
    database_url: str = os.getenv("DATABASE_URL", "")

    # Logging
    log_level: str = os.getenv("MCP_LOG_LEVEL", "INFO")

    # Feature flags
    enable_database_tools: bool = True  # Enable tools that query the database


# Global config instance
config = MCPConfig()
