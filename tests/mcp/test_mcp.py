"""
Tests for MCP server functionality.
"""

import pytest

from app.mcp.resources import list_resources, read_resource
from app.mcp.tools import call_tool, list_tools


class TestResources:
    """Test MCP resources."""

    @pytest.mark.asyncio
    async def test_list_resources(self):
        """Test that list_resources returns expected resources."""
        resources = await list_resources()

        assert len(resources) == 2
        assert any(str(r.uri) == "knowledge-graph://stats" for r in resources)
        assert any(str(r.uri) == "aether://info" for r in resources)

    @pytest.mark.asyncio
    async def test_read_graph_stats(self):
        """Test reading knowledge graph stats resource."""
        content = await read_resource("knowledge-graph://stats")

        assert content is not None
        assert "total_nodes" in content
        assert "mock_data" in content  # Currently returns mock data

    @pytest.mark.asyncio
    async def test_read_system_info(self):
        """Test reading system info resource."""
        content = await read_resource("aether://info")

        assert content is not None
        assert "Aether" in content
        assert "FSRS" in content

    @pytest.mark.asyncio
    async def test_read_invalid_resource(self):
        """Test that reading an invalid resource raises ValueError."""
        with pytest.raises(ValueError, match="Unknown resource URI"):
            await read_resource("invalid://resource")


class TestTools:
    """Test MCP tools."""

    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test that list_tools returns expected tools."""
        tools = await list_tools()

        assert len(tools) == 2
        assert any(t.name == "echo" for t in tools)
        assert any(t.name == "get_node_info" for t in tools)

    @pytest.mark.asyncio
    async def test_echo_tool(self):
        """Test the echo tool."""
        result = await call_tool("echo", {"message": "Hello, MCP!"})

        assert len(result) == 1
        assert result[0].type == "text"
        assert "Hello, MCP!" in result[0].text

    @pytest.mark.asyncio
    async def test_get_node_info_tool(self):
        """Test the get_node_info tool."""
        result = await call_tool("get_node_info", {"node_name": "Photosynthesis"})

        assert len(result) == 1
        assert result[0].type == "text"
        assert "Photosynthesis" in result[0].text
        assert "Mock Data" in result[0].text  # Currently returns mock data

    @pytest.mark.asyncio
    async def test_call_invalid_tool(self):
        """Test that calling an invalid tool raises ValueError."""
        with pytest.raises(ValueError, match="Unknown tool"):
            await call_tool("invalid_tool", {})
