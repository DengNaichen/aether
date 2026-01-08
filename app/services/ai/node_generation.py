import logging
from dataclasses import dataclass
from pathlib import Path

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.prompts import (
    GRAPH_GEN_FEW_SHOT_EXAMPLES,
    GRAPH_GEN_SYSTEM_PROMPT,
)
from app.schemas.knowledge_node import KnowledgeNodeLLM, KnowledgeNodesLLM
from app.utils.split_text import split_text_content

# Configuration defaults (centralized in settings)
DEFAULT_MODEL_NAME = settings.GEMINI_GRAPH_MODEL
DEFAULT_MODEL_TEMPERATURE = settings.GEMINI_GRAPH_TEMPERATURE
DEFAULT_MAX_RETRY_ATTEMPTS = settings.GEMINI_GRAPH_MAX_RETRY_ATTEMPTS
DEFAULT_CHUNK_SIZE = settings.GEMINI_GRAPH_CHUNK_SIZE  # ~75k tokens
DEFAULT_CHUNK_OVERLAP = settings.GEMINI_GRAPH_CHUNK_OVERLAP  # ~2.5k tokens


@dataclass
class PipelineConfig:
    """Configuration for the knowledge graph extraction pipeline."""

    model_name: str = DEFAULT_MODEL_NAME
    temperature: float = DEFAULT_MODEL_TEMPERATURE
    max_retry_attempts: int = DEFAULT_MAX_RETRY_ATTEMPTS
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP


# Configure Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Raised when the Google API key is not configured."""

    pass


def _get_client(api_key: str | None = None):
    """Initialize Google GenAI Client."""
    api_key = api_key or settings.GOOGLE_API_KEY
    if not api_key:
        raise MissingAPIKeyError(
            "GOOGLE_API_KEY is not set in settings. "
            "Please configure it before running the pipeline."
        )
    return genai.Client(api_key=api_key)


def _create_extract_with_retry(max_attempts: int, model_name: str, temperature: float):
    """Factory function to create extract function with configurable retry."""

    @retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def _extract(
        client: genai.Client, content: str, user_guidance: str = ""
    ) -> KnowledgeNodesLLM:
        formatted_system_prompt = GRAPH_GEN_SYSTEM_PROMPT.format(
            user_guidance=(
                f"### Extra Instructions:\n{user_guidance}" if user_guidance else ""
            )
        )

        full_prompt = (
            f"{formatted_system_prompt}\n\n"
            f"### Few-Shot Examples\n{GRAPH_GEN_FEW_SHOT_EXAMPLES}\n\n"
            f"### Input Text to Analyze\n{content}"
        )

        response = client.models.generate_content(
            model=model_name,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=KnowledgeNodesLLM,
                temperature=temperature,
            ),
        )

        if not response.parsed:
            raise ValueError("Failed to parse LLM response into KnowledgeNodesLLM")

        return response.parsed

    return _extract


# TODO: Keep this pipeline output limited to KnowledgeNodesLLM.
def generate_nodes_from_markdown(
    md_path: str | Path,
    user_guidance: str = "",
    config: PipelineConfig | None = None,
) -> KnowledgeNodesLLM:
    """
    Process a Markdown file and extract a knowledge graph.
    Supports incremental processing for large files.

    Args:
        md_path: Path to the Markdown file.
        user_guidance: Additional instructions for the LLM.
        config: Pipeline configuration. Uses defaults if not provided.

    Returns:
        KnowledgeNodesLLM with extracted nodes (empty list on failure).

    Raises:
        MissingAPIKeyError: If GOOGLE_API_KEY is not set.
        FileNotFoundError: If the Markdown file does not exist.
    """
    config = config or PipelineConfig()

    path = Path(md_path)
    if not path.exists():
        raise FileNotFoundError(f"Markdown file not found: {path}")

    logger.info(f"Loading Markdown: {path}")
    content = path.read_text(encoding="utf-8")

    if not content.strip():
        logger.warning(f"Markdown is empty: {path}")
        return KnowledgeNodesLLM(nodes=[])

    client = _get_client()
    extract = _create_extract_with_retry(
        config.max_retry_attempts, config.model_name, config.temperature
    )

    # 1. Split content
    chunks = split_text_content(content, config.chunk_size, config.chunk_overlap)
    logger.info(
        f"Split content into {len(chunks)} chunks (Size: {config.chunk_size}, Overlap: {config.chunk_overlap})"
    )

    # 2. Extract from chunks
    extracted_nodes: list[KnowledgeNodeLLM] = []

    for i, chunk in enumerate(chunks):
        logger.info(f"Processing chunk {i + 1}/{len(chunks)} ({len(chunk)} chars)...")
        try:
            chunk_guidance = user_guidance
            if len(chunks) > 1:
                chunk_guidance += (
                    f"\n(Processing part {i + 1} of {len(chunks)} of the document)"
                )

            graph = extract(client, chunk, chunk_guidance)
            extracted_nodes.extend(graph.nodes)
            logger.info(f"Chunk {i + 1}: Found {len(graph.nodes)} nodes")
        except Exception as e:
            logger.error(f"Failed to extract from chunk {i + 1}: {e}")
            # Continue with other chunks instead of failing completely?
            # ideally we want partial results
            continue

    if not extracted_nodes:
        logger.warning("No graphs extracted from any chunks.")
        return KnowledgeNodesLLM(nodes=[])

    final_nodes = KnowledgeNodesLLM(nodes=extracted_nodes)
    logger.info(f"Final: {len(final_nodes.nodes)} nodes")
    return final_nodes
