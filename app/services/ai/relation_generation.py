"""
Relation Generation Service - Generate prerequisite relationships using LLM.

This service takes a list of knowledge nodes and optionally existing edges,
then calls LLM to generate new prerequisite relationships.
"""

import logging
from dataclasses import dataclass

from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.prompts import RELATION_GEN_SYSTEM_PROMPT
from app.schemas.knowledge_node import KnowledgeNodeLLM, PrerequisiteLLM
from app.services.ai.common import get_genai_client

# Configuration defaults
DEFAULT_MODEL_NAME = settings.GEMINI_GRAPH_MODEL
DEFAULT_MODEL_TEMPERATURE = settings.GEMINI_GRAPH_TEMPERATURE
DEFAULT_MAX_RETRY_ATTEMPTS = settings.GEMINI_GRAPH_MAX_RETRY_ATTEMPTS

logger = logging.getLogger(__name__)


@dataclass
class RelationGenerationConfig:
    """Configuration for relation generation."""

    model_name: str = DEFAULT_MODEL_NAME
    temperature: float = DEFAULT_MODEL_TEMPERATURE
    max_retry_attempts: int = DEFAULT_MAX_RETRY_ATTEMPTS


class PrerequisitesLLM(BaseModel):
    """Container for LLM-generated prerequisites."""

    prerequisites: list[PrerequisiteLLM] = Field(default_factory=list)


def _format_nodes_for_prompt(nodes: list[KnowledgeNodeLLM]) -> str:
    """Format nodes as a readable list for the prompt."""
    lines = []
    for node in nodes:
        lines.append(f"- {node.name}: {node.description}")
    return "\n".join(lines)


def _format_edges_for_prompt(edges: list[PrerequisiteLLM]) -> str:
    """Format existing edges as a readable list for the prompt."""
    if not edges:
        return "(No existing relationships)"
    lines = []
    for edge in edges:
        lines.append(f"- {edge.source_name} → {edge.target_name}")
    return "\n".join(lines)


def _create_generate_with_retry(max_attempts: int, model_name: str, temperature: float):
    """Factory function to create generate function with configurable retry."""

    @retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def _generate(
        client: genai.Client,
        nodes: list[KnowledgeNodeLLM],
        existing_edges: list[PrerequisiteLLM] | None = None,
    ) -> PrerequisitesLLM:
        nodes_text = _format_nodes_for_prompt(nodes)
        edges_text = _format_edges_for_prompt(existing_edges or [])

        user_prompt = f"""### All Nodes in the Graph
{nodes_text}

### Existing Prerequisite Relationships
{edges_text}

Generate ONLY NEW prerequisite relationships. Do NOT repeat any existing relationships listed above.
"""

        response = client.models.generate_content(
            model=model_name,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part(text=RELATION_GEN_SYSTEM_PROMPT)],
                ),
                types.Content(
                    role="user",
                    parts=[types.Part(text=user_prompt)],
                ),
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PrerequisitesLLM,
                temperature=temperature,
            ),
        )

        if not response.parsed:
            raise ValueError("Failed to parse LLM response into PrerequisitesLLM")

        return response.parsed

    return _generate


def generate_relations(
    nodes: list[KnowledgeNodeLLM],
    existing_edges: list[PrerequisiteLLM] | None = None,
    config: RelationGenerationConfig | None = None,
) -> list[PrerequisiteLLM]:
    """
    Generate new prerequisite relationships between nodes.

    Args:
        nodes: All nodes in the graph
        existing_edges: Already existing edges (to avoid duplicates)
        config: Generation configuration. Uses defaults if not provided.

    Returns:
        List of new prerequisite relationships

    Raises:
        MissingAPIKeyError: If GOOGLE_API_KEY is not set.
    """
    config = config or RelationGenerationConfig()

    if not nodes:
        logger.warning("No nodes provided, returning empty list")
        return []

    if len(nodes) < 2:
        logger.warning("Less than 2 nodes, no relationships possible")
        return []

    logger.info(
        f"Generating relations for {len(nodes)} nodes "
        f"(existing edges: {len(existing_edges) if existing_edges else 0})"
    )

    client = get_genai_client()
    generate = _create_generate_with_retry(
        config.max_retry_attempts, config.model_name, config.temperature
    )

    result = generate(client, nodes, existing_edges)

    logger.info(f"Generated {len(result.prerequisites)} new relationships")
    return result.prerequisites
