import logging
import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.schemas.knowledge_node import GraphStructureLLM, RelationshipType

# Configuration defaults
DEFAULT_MODEL_NAME = "gemini-3-pro-preview"
DEFAULT_MODEL_TEMPERATURE = 0
DEFAULT_MAX_RETRY_ATTEMPTS = 3


@dataclass
class PipelineConfig:
    """Configuration for the knowledge graph extraction pipeline."""
    model_name: str = DEFAULT_MODEL_NAME
    temperature: float = DEFAULT_MODEL_TEMPERATURE
    max_retry_attempts: int = DEFAULT_MAX_RETRY_ATTEMPTS


# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Extraction Prompt ---

SYSTEM_PROMPT = """
You are an expert Knowledge Graph Engineer specializing in extracting **Teachable Knowledge Units** for an educational assessment system.

### Core Definitions:
- **KnowledgeNode**: A **teachable concept** that can be independently tested with quiz questions.
- **IS_PREREQUISITE_FOR**: Dependency relation. Concept A must be learned before Concept B.
- **HAS_SUBTOPIC**: Hierarchical relation. Parent -> Child.

### CRITICAL: Node Granularity Rules

A node should be the **smallest teachable unit** - something a student can learn and be tested on.

**DO extract as nodes:**
- Core concepts (e.g., "Significant Digits", "Physical Properties", "Chemical Changes")
- Laws, principles, theories (e.g., "Newton's Second Law", "Law of Conservation of Mass")
- Important processes (e.g., "Photosynthesis", "Eutrophication")
- Key classifications (e.g., "Pure Substances vs Mixtures", "Elements vs Compounds")

**DO NOT extract as separate nodes:**
- Simple examples or instances (e.g., "Red", "Blue" as colors - these are just examples)
- Individual rules or steps (e.g., "Rounding Up when > 5" - this is part of "Rounding Rules")
- Properties that are just list items (e.g., "Colour", "Odour" - include in parent's description)
- Trivial definitions (e.g., "Metre is a unit" - too simple to test)

### Quality Check:
Before creating a node, ask: "Can I write a meaningful quiz question to test this concept?"
- If YES → Create the node
- If NO → It's probably an example or detail that belongs in a parent node's description

### Relationship Rules:
1. **IS_PREREQUISITE_FOR**: Only use when understanding A is truly required before B
2. **HAS_SUBTOPIC**: Use for hierarchical breakdown of major topics

{user_guidance}
"""

FEW_SHOT_EXAMPLES = [
    ("human", "Text: The three primary colors are Red, Blue, and Yellow. Secondary colors are made by mixing two primary colors."),
    ("ai", """{{
  "nodes": [
    {{"name": "Primary Colors", "description": "The three base colors (Red, Blue, Yellow) that cannot be created by mixing other colors."}},
    {{"name": "Secondary Colors", "description": "Colors created by mixing two primary colors together."}}
  ],
  "relationships": [
    {{"source_name": "Primary Colors", "target_name": "Secondary Colors", "label": "IS_PREREQUISITE_FOR"}}
  ]
}}"""),
    ("human", "Text: Significant digits are the digits in a measurement that are known with certainty plus one estimated digit. Rules: All non-zero digits are significant. Zeros between non-zero digits are significant. Leading zeros are not significant."),
    ("ai", """{{
  "nodes": [
    {{"name": "Significant Digits", "description": "The digits in a measurement that are known with certainty plus one estimated digit. Rules include: all non-zero digits are significant, zeros between non-zero digits are significant, and leading zeros are not significant."}}
  ],
  "relationships": []
}}"""),
    ("human", "Text: To understand Calculus, you must first learn Limits. Calculus includes Derivatives and Integrals. A derivative measures the rate of change of a function."),
    ("ai", """{{
  "nodes": [
    {{"name": "Calculus", "description": "Branch of mathematics studying continuous change, built upon the concept of limits."}},
    {{"name": "Limits", "description": "Foundational concept describing the behavior of a function as its input approaches a particular value."}},
    {{"name": "Derivatives", "description": "A measure of the rate of change of a function, representing instantaneous rate of change."}},
    {{"name": "Integrals", "description": "The accumulation of quantities, mathematically the reverse operation of derivatives."}}
  ],
  "relationships": [
    {{"source_name": "Limits", "target_name": "Derivatives", "label": "IS_PREREQUISITE_FOR"}},
    {{"source_name": "Limits", "target_name": "Integrals", "label": "IS_PREREQUISITE_FOR"}},
    {{"parent_name": "Calculus", "child_name": "Derivatives", "label": "HAS_SUBTOPIC"}},
    {{"parent_name": "Calculus", "child_name": "Integrals", "label": "HAS_SUBTOPIC"}}
  ]
}}"""),
]

# --- Refinement Prompt ---

FIX_SYSTEM_PROMPT = """
You are a Knowledge Graph Refinement Agent.
Your task is to FIX 'Prerequisite Relationships' that point to broad 'Parent Topics' instead of specific 'Atomic Concepts'.

I will provide a list of INVALID relationships where a Concept depends on a Parent Topic.
I will also list the specific Children of that Parent Topic.

**Task:**
Re-route the dependency to the specific Child Node(s) that truly require the prerequisite.
Return a list of NEW relationships. Leave the 'nodes' list empty.
"""

FIX_USER_TEMPLATE = """
Here are the Logic Violations detected in the graph:

{violations}

Please generate corrected 'IS_PREREQUISITE_FOR' relationships connecting the Source to the specific Children.
"""


class MissingAPIKeyError(Exception):
    """Raised when the Google API key is not configured."""
    pass


def _get_llm(config: PipelineConfig):
    """Initialize LLM with structured output capability."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise MissingAPIKeyError(
            "GOOGLE_API_KEY environment variable is not set. "
            "Please set it before running the pipeline."
        )

    llm = ChatGoogleGenerativeAI(
        model=config.model_name,
        temperature=config.temperature,
        google_api_key=api_key
    )
    return llm.with_structured_output(GraphStructureLLM)


def _create_extract_with_retry(max_attempts: int):
    """Factory function to create extract function with configurable retry."""
    @retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def _extract(llm_struct, content: str, user_guidance: str = "") -> GraphStructureLLM:
        formatted_system_prompt = SYSTEM_PROMPT.format(
            user_guidance=f"### Extra Instructions:\n{user_guidance}" if user_guidance else ""
        )
        prompt_messages = [("system", formatted_system_prompt)]
        prompt_messages.extend(FEW_SHOT_EXAMPLES)
        prompt_messages.append(("human", "Text to analyze:\n{text}"))

        prompt = ChatPromptTemplate.from_messages(prompt_messages)
        chain = prompt | llm_struct
        return chain.invoke({"text": content})
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
        nodes=list(merged_nodes.values()),
        relationships=merged_rels
    )


def _get_relationship_signature(rel: RelationshipType) -> str:
    """Get a unique signature for a relationship for comparison."""
    if rel.label == "IS_PREREQUISITE_FOR":
        return f"PRE:{rel.source_id}->{rel.target_id}"
    else:
        return f"SUB:{rel.parent_id}->{rel.child_id}"


def refine_graph_with_llm(
    graph: GraphStructureLLM,
    llm_struct,
    max_retry_attempts: int = DEFAULT_MAX_RETRY_ATTEMPTS
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
        return [r for r in rels if _get_relationship_signature(r) not in bad_rel_signatures]

    # Step C: AI Fix with retry
    @retry(
        stop=stop_after_attempt(max_retry_attempts),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def call_ai_fix(violations_text: str) -> GraphStructureLLM:
        prompt = ChatPromptTemplate.from_messages([
            ("system", FIX_SYSTEM_PROMPT),
            ("human", FIX_USER_TEMPLATE)
        ])
        chain = prompt | llm_struct
        return chain.invoke({"violations": violations_text})

    try:
        fix_result = call_ai_fix("\n".join(violations_desc))

        if not fix_result or not fix_result.relationships:
            logger.warning("AI returned no fixes. Falling back to simple removal.")
            return GraphStructureLLM(nodes=graph.nodes, relationships=filter_bad_rels(graph.relationships))

        logger.info(f"AI suggested {len(fix_result.relationships)} corrected relationships.")

        kept_rels = filter_bad_rels(graph.relationships)
        final_rels = kept_rels + fix_result.relationships

        return GraphStructureLLM(nodes=graph.nodes, relationships=final_rels)

    except Exception as e:
        logger.error(f"AI Refinement failed after {max_retry_attempts} attempts: {e}. Falling back to simple removal.")
        return GraphStructureLLM(nodes=graph.nodes, relationships=filter_bad_rels(graph.relationships))


# --- Main Process ---

def process_markdown(
    md_path: str | Path,
    user_guidance: str = "",
    config: PipelineConfig | None = None,
) -> GraphStructureLLM | None:
    """
    Process a Markdown file and extract a knowledge graph.

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

    llm_struct = _get_llm(config)
    extract = _create_extract_with_retry(config.max_retry_attempts)

    # Extract graph from content
    logger.info(f"Extracting graph from {path.name} ({len(content)} chars)...")

    try:
        graph = extract(llm_struct, content, user_guidance)
        logger.info(f"Extracted: {len(graph.nodes)} nodes, {len(graph.relationships)} relationships")
    except Exception as e:
        logger.error(f"Failed to extract graph: {e}")
        return None

    # Refine graph
    logger.info("Refining graph...")
    final_graph = refine_graph_with_llm(graph, llm_struct, config.max_retry_attempts)

    logger.info(f"Final: {len(final_graph.nodes)} nodes, {len(final_graph.relationships)} relationships")
    return final_graph
