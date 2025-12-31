"""
Graph generation response schema.
"""
from pydantic import BaseModel, Field


class GraphGenerationResponse(BaseModel):
    """Response schema for graph generation from markdown."""
    
    graph_id: str = Field(..., description="Graph UUID")
    nodes_created: int = Field(..., description="Number of new nodes created")
    prerequisites_created: int = Field(
        ..., description="Number of prerequisite relationships created"
    )
    total_nodes: int = Field(..., description="Total nodes in graph after generation")
    max_level: int = Field(..., description="Maximum topological level in the graph")
    message: str = Field(..., description="Success message")
