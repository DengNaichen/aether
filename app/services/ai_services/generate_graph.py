import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.prompts import (
    GRAPH_FIX_SYSTEM_PROMPT,
    GRAPH_FIX_USER_TEMPLATE,
    GRAPH_GEN_FEW_SHOT_EXAMPLES,
    GRAPH_GEN_SYSTEM_PROMPT,
)
from app.schemas.knowledge_node import GraphStructureLLM, RelationshipType
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
    ) -> GraphStructureLLM:
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
                response_schema=GraphStructureLLM,
                temperature=temperature,
            ),
        )

        if not response.parsed:
            raise ValueError("Failed to parse LLM response into GraphStructureLLM")

        return response.parsed

    return _extract


def merge_graphs(graphs: list[GraphStructureLLM]) -> GraphStructureLLM:
    """Merges multiple graphs, deduplicating nodes and relationships."""
    merged_nodes = {}
    merged_rels = []
    seen_rels = set()

    for g in graphs:
        for node in g.nodes:
            if node.id not in merged_nodes:
                merged_nodes[node.id] = node
            else:
                # Keep the one with longer description
                if len(node.description) > len(merged_nodes[node.id].description):
                    merged_nodes[node.id] = node

        for rel in g.relationships:
            sig = _get_relationship_signature(rel)
            if sig not in seen_rels:
                seen_rels.add(sig)
                merged_rels.append(rel)

    return GraphStructureLLM(
        nodes=list(merged_nodes.values()), relationships=merged_rels
    )


def _get_relationship_signature(rel: RelationshipType) -> str:
    """Get a unique signature for a relationship for comparison."""
    if rel.label == "IS_PREREQUISITE_FOR":
        return f"PRE:{rel.source_id}->{rel.target_id}"
    else:
        return f"SUB:{rel.parent_id}->{rel.child_id}"


def refine_graph_with_llm(
    graph: GraphStructureLLM,
    client: genai.Client,
    config: PipelineConfig,
) -> GraphStructureLLM:
    """
    1. Local Check: Finds prerequisites pointing to 'Parent Nodes'.
    2. AI Fix: Asks LLM to re-route these prerequisites to specific children.
    """
    logger.info("Starting Local Logic Detection...")

    # Step A: Map Parents to their Children
    parent_to_children = defaultdict(list)
    for rel in graph.relationships:
        if rel.label == "HAS_SUBTOPIC" and rel.child_name:
            parent_to_children[rel.parent_id].append(rel.child_name)

    # Step B: Identify Violations
    bad_rel_signatures: set[str] = set()
    violations_desc: list[str] = []

    for rel in graph.relationships:
        if rel.label == "IS_PREREQUISITE_FOR":
            if rel.target_id in parent_to_children:
                bad_rel_signatures.add(_get_relationship_signature(rel))
                children_str = ", ".join(parent_to_children[rel.target_id])
                desc = f"- Violation: '{rel.source_name}' is a Prerequisite for Parent Topic '{rel.target_name}'. \n  Context: '{rel.target_name}' contains: [{children_str}].\n"
                violations_desc.append(desc)

    if not bad_rel_signatures:
        logger.info("No logic violations found. Graph is clean.")
        return graph

    logger.info(f"Found {len(bad_rel_signatures)} violations. Asking AI to fix...")

    def filter_bad_rels(rels: list[RelationshipType]) -> list[RelationshipType]:
        return [
            r for r in rels if _get_relationship_signature(r) not in bad_rel_signatures
        ]

    # Step C: AI Fix with retry
    @retry(
        stop=stop_after_attempt(config.max_retry_attempts),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def call_ai_fix(violations_text: str) -> GraphStructureLLM:
        prompt_content = GRAPH_FIX_USER_TEMPLATE.format(violations=violations_text)
        full_prompt = f"{GRAPH_FIX_SYSTEM_PROMPT}\n\n{prompt_content}"

        response = client.models.generate_content(
            model=config.model_name,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=GraphStructureLLM,
                temperature=config.temperature,
            ),
        )

        if not response.parsed:
            raise ValueError("Failed to parse LLM response for fix")
        return response.parsed

    try:
        fix_result = call_ai_fix("\n".join(violations_desc))

        if not fix_result or not fix_result.relationships:
            logger.warning("AI returned no fixes. Falling back to simple removal.")
            return GraphStructureLLM(
                nodes=graph.nodes, relationships=filter_bad_rels(graph.relationships)
            )

        logger.info(
            f"AI suggested {len(fix_result.relationships)} corrected relationships."
        )

        kept_rels = filter_bad_rels(graph.relationships)
        final_rels = kept_rels + fix_result.relationships

        return GraphStructureLLM(nodes=graph.nodes, relationships=final_rels)

    except Exception as e:
        logger.error(
            f"AI Refinement failed after {config.max_retry_attempts} attempts: {e}. Falling back to simple removal."
        )
        return GraphStructureLLM(
            nodes=graph.nodes, relationships=filter_bad_rels(graph.relationships)
        )


# --- Main Process ---


def process_markdown(
    md_path: str | Path,
    user_guidance: str = "",
    config: PipelineConfig | None = None,
) -> GraphStructureLLM | None:
    """
    Process a Markdown file and extract a knowledge graph.
    Supports incremental processing for large files.

    Args:
        md_path: Path to the Markdown file.
        user_guidance: Additional instructions for the LLM.
        config: Pipeline configuration. Uses defaults if not provided.

    Returns:
        GraphStructureLLM with extracted nodes and relationships, or None if failed.

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
        return GraphStructureLLM(nodes=[], relationships=[])

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
    extracted_graphs = []

    for i, chunk in enumerate(chunks):
        logger.info(f"Processing chunk {i+1}/{len(chunks)} ({len(chunk)} chars)...")
        try:
            chunk_guidance = user_guidance
            if len(chunks) > 1:
                chunk_guidance += (
                    f"\n(Processing part {i+1} of {len(chunks)} of the document)"
                )

            graph = extract(client, chunk, chunk_guidance)
            extracted_graphs.append(graph)
            logger.info(
                f"Chunk {i+1}: Found {len(graph.nodes)} nodes, {len(graph.relationships)} rels"
            )
        except Exception as e:
            logger.error(f"Failed to extract from chunk {i+1}: {e}")
            # Continue with other chunks instead of failing completely?
            # ideally we want partial results
            continue

    if not extracted_graphs:
        logger.warning("No graphs extracted from any chunks.")
        return GraphStructureLLM(nodes=[], relationships=[])

    # 3. Merge graphs
    logger.info("Merging chunk graphs...")
    merged_graph = merge_graphs(extracted_graphs)
    logger.info(
        f"Merged Result: {len(merged_graph.nodes)} nodes, {len(merged_graph.relationships)} relationships"
    )

    # 4. Refine final graph
    logger.info("Refining final graph...")
    final_graph = refine_graph_with_llm(merged_graph, client, config)

    logger.info(
        f"Final: {len(final_graph.nodes)} nodes, {len(final_graph.relationships)} relationships"
    )
    return final_graph
