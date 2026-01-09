"""
Gemini SDK pipeline for generating quiz questions from knowledge graph nodes.

This pipeline follows the same pattern as generate_graph.py:
- Uses Google Gemini with structured output
- Few-shot examples for consistent formatting
- Retry logic with exponential backoff
- Configurable via PipelineConfig
"""

import logging
from dataclasses import dataclass
from typing import Literal

from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.prompts import (
    QUESTION_GEN_FEW_SHOT_EXAMPLES,
    QUESTION_GEN_SYSTEM_PROMPT,
)
from app.services.ai.common import get_genai_client

# Configuration defaults (centralized in settings)
DEFAULT_MODEL_NAME = settings.GEMINI_QUESTION_MODEL
DEFAULT_MODEL_TEMPERATURE = (
    settings.GEMINI_QUESTION_TEMPERATURE  # Slightly higher for creative questions
)
DEFAULT_MAX_RETRY_ATTEMPTS = settings.GEMINI_QUESTION_MAX_RETRY_ATTEMPTS

# Configure Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


logger = logging.getLogger(__name__)


# ==================== Pydantic Schemas for LLM Output ====================


class QuestionOptionLLM(BaseModel):
    """A single option for multiple choice questions."""

    text: str = Field(description="The option text")
    is_correct: bool = Field(description="Whether this is the correct answer")


class GeneratedQuestionLLM(BaseModel):
    """A single generated question from the LLM."""

    question_type: Literal["multiple_choice", "fill_blank", "short_answer"] = Field(
        description="Type of question"
    )
    text: str = Field(description="The question text/prompt")
    difficulty: Literal["easy", "medium", "hard"] = Field(
        description="Question difficulty level"
    )
    # For multiple choice
    options: list[QuestionOptionLLM] | None = Field(
        default=None, description="Options for multiple choice (4 options required)"
    )
    # For fill_blank and short_answer
    expected_answers: list[str] | None = Field(
        default=None, description="Acceptable answers for fill_blank/short_answer"
    )
    explanation: str = Field(
        description="Brief explanation of why the answer is correct"
    )


class QuestionBatchLLM(BaseModel):
    """Batch of generated questions for a single knowledge node."""

    questions: list[GeneratedQuestionLLM] = Field(
        description="List of generated questions"
    )


class NodeQuestionBatchLLM(BaseModel):
    """Questions generated for a specific node."""

    node_name: str = Field(description="Name of the knowledge node")
    questions: list[GeneratedQuestionLLM] = Field(
        description="List of generated questions for this node"
    )


class MultiNodeQuestionBatchLLM(BaseModel):
    """Batch of questions generated for multiple nodes in one call."""

    node_batches: list[NodeQuestionBatchLLM] = Field(
        description="List of question batches, one per node"
    )


# ==================== Pipeline Configuration ====================


@dataclass
class PipelineConfig:
    """Configuration for the question generation pipeline."""

    model_name: str = DEFAULT_MODEL_NAME
    temperature: float = DEFAULT_MODEL_TEMPERATURE
    max_retry_attempts: int = DEFAULT_MAX_RETRY_ATTEMPTS


# ==================== LLM Initialization ====================


def _build_prompt_contents(
    formatted_system_prompt: str,
    user_message: str,
) -> list[types.Content]:
    """Build GenAI contents with few-shot examples and user input."""
    contents = [
        types.Content(role="user", parts=[types.Part(text=formatted_system_prompt)])
    ]

    for role, text in QUESTION_GEN_FEW_SHOT_EXAMPLES:
        role_key = role.lower()
        genai_role = "user" if role_key in {"human", "user"} else "model"
        normalized_text = text.strip().replace("{{", "{").replace("}}", "}")
        contents.append(
            types.Content(role=genai_role, parts=[types.Part(text=normalized_text)])
        )

    contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))
    return contents


def _format_difficulty_distribution(
    num_questions: int, difficulty_distribution: dict | None
) -> str:
    """Format difficulty distribution instruction string."""
    if difficulty_distribution:
        return ", ".join(
            f"{count} {level}" for level, count in difficulty_distribution.items()
        )

    easy = num_questions // 3
    hard = num_questions // 3
    medium = num_questions - easy - hard
    return f"{easy} easy, {medium} medium, {hard} hard"


def _format_question_type_preference(question_types: list[str] | None) -> str:
    """Format question type preference instruction string."""
    if not question_types:
        return ""
    return f"\nPreferred question types: {', '.join(question_types)}"


def _format_system_prompt(user_guidance: str) -> str:
    """Format the system prompt with optional guidance."""
    extra_guidance = (
        f"### Extra Instructions:\n{user_guidance}" if user_guidance else ""
    )
    return QUESTION_GEN_SYSTEM_PROMPT.format(user_guidance=extra_guidance)


def _build_single_node_message(
    node_name: str,
    node_description: str,
    num_questions: int,
    diff_str: str,
    type_str: str,
) -> str:
    """Build the user message for single-node generation."""
    return f"""
Node Name: {node_name}
Node Description: {node_description}

Generate {num_questions} questions ({diff_str}).{type_str}
"""


def _build_batch_message(
    valid_nodes: list[dict],
    questions_per_node: int,
    diff_str: str,
    type_str: str,
) -> str:
    """Build the user message for batch generation."""
    nodes_description = "\n\n".join(
        [
            f"Node {i + 1}: {node['name']}\nDescription: {node['description']}"
            for i, node in enumerate(valid_nodes)
        ]
    )

    return f"""
I have {len(valid_nodes)} knowledge nodes. For EACH node, generate {questions_per_node} questions ({diff_str}).{type_str}

{nodes_description}

IMPORTANT: Return a JSON object with a "node_batches" array. Each element should have:
- "node_name": exact name of the node
- "questions": array of {questions_per_node} questions for that node

Generate questions for ALL {len(valid_nodes)} nodes.
"""


def _generate_with_schema(
    client: genai.Client,
    model_name: str,
    temperature: float,
    response_schema: type[BaseModel],
    formatted_system_prompt: str,
    user_message: str,
):
    """Generate content with a structured output schema."""
    response = client.models.generate_content(
        model=model_name,
        contents=_build_prompt_contents(formatted_system_prompt, user_message),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=temperature,
        ),
    )

    if not response.parsed:
        raise ValueError(
            f"Failed to parse LLM response into {response_schema.__name__}"
        )

    return response.parsed


# ==================== Question Generation ====================


def _create_generate_with_retry(
    max_attempts: int,
    model_name: str,
    temperature: float,
):
    """Factory function to create generate function with configurable retry."""

    @retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def _generate(
        client: genai.Client,
        node_name: str,
        node_description: str,
        num_questions: int = 3,
        difficulty_distribution: dict | None = None,
        question_types: list[str] | None = None,
        user_guidance: str = "",
    ) -> QuestionBatchLLM:
        """Generate questions for a single knowledge node."""

        diff_str = _format_difficulty_distribution(
            num_questions, difficulty_distribution
        )
        type_str = _format_question_type_preference(question_types)
        formatted_system_prompt = _format_system_prompt(user_guidance)
        user_message = _build_single_node_message(
            node_name, node_description, num_questions, diff_str, type_str
        )

        return _generate_with_schema(
            client,
            model_name,
            temperature,
            QuestionBatchLLM,
            formatted_system_prompt,
            user_message,
        )

    return _generate


def generate_questions_for_node(
    node_name: str,
    node_description: str,
    num_questions: int = 3,
    difficulty_distribution: dict | None = None,
    question_types: list[str] | None = None,
    user_guidance: str = "",
    config: PipelineConfig | None = None,
) -> QuestionBatchLLM | None:
    """
    Generate quiz questions for a single knowledge node.

    Args:
        node_name: Name of the knowledge concept (e.g., "Photosynthesis")
        node_description: Description of the concept
        num_questions: Number of questions to generate (default: 3)
        difficulty_distribution: Dict like {"easy": 1, "medium": 1, "hard": 1}
        question_types: List of preferred types ["multiple_choice", "fill_blank", "short_answer"]
        user_guidance: Additional instructions for the LLM
        config: Pipeline configuration

    Returns:
        QuestionBatchLLM with generated questions, or None if failed

    Raises:
        MissingAPIKeyError: If GOOGLE_API_KEY is not set
    """
    config = config or PipelineConfig()

    if not node_name or not node_description:
        logger.warning("Node name and description are required")
        return None

    client = get_genai_client()
    generate = _create_generate_with_retry(
        config.max_retry_attempts, config.model_name, config.temperature
    )

    logger.info(f"Generating {num_questions} questions for node: {node_name}")

    try:
        result = generate(
            client,
            node_name,
            node_description,
            num_questions,
            difficulty_distribution,
            question_types,
            user_guidance,
        )
        logger.info(f"Generated {len(result.questions)} questions successfully")
        return result
    except Exception as e:
        logger.error(f"Failed to generate questions: {e}")
        return None


def generate_questions_for_nodes_batch(
    nodes: list[dict],
    questions_per_node: int = 3,
    difficulty_distribution: dict | None = None,
    question_types: list[str] | None = None,
    user_guidance: str = "",
    config: PipelineConfig | None = None,
) -> MultiNodeQuestionBatchLLM | None:
    """
    Generate questions for multiple nodes in a SINGLE LLM call (batch mode).

    This is much more efficient than calling generate_questions_for_node()
    per node. Use this when you have many nodes and want to save on API quota.

    Args:
        nodes: List of dicts with 'name' and 'description' keys
        questions_per_node: Number of questions per node
        difficulty_distribution: Dict like {"easy": 1, "medium": 1, "hard": 1}
        question_types: List of preferred types
        user_guidance: Additional instructions
        config: Pipeline configuration

    Returns:
        MultiNodeQuestionBatchLLM with all generated questions, or None if failed

    Example:
        nodes = [
            {"name": "Photosynthesis", "description": "Process by which..."},
            {"name": "Cellular Respiration", "description": "Process of..."}
        ]
        result = generate_questions_for_nodes_batch(nodes, questions_per_node=3)
        # Returns questions for ALL nodes in one call!
    """
    config = config or PipelineConfig()

    if not nodes:
        logger.warning("No nodes provided for batch generation")
        return None

    # Filter out invalid nodes
    valid_nodes = [n for n in nodes if n.get("name") and n.get("description")]

    if not valid_nodes:
        logger.warning(
            "No valid nodes (with name and description) for batch generation"
        )
        return None

    logger.info(
        f"Batch generating questions for {len(valid_nodes)} nodes in ONE LLM call"
    )

    diff_str = _format_difficulty_distribution(
        questions_per_node, difficulty_distribution
    )
    type_str = _format_question_type_preference(question_types)
    formatted_system_prompt = _format_system_prompt(user_guidance)
    user_message = _build_batch_message(
        valid_nodes, questions_per_node, diff_str, type_str
    )

    try:
        client = get_genai_client()

        result = _generate_with_schema(
            client,
            config.model_name,
            config.temperature,
            MultiNodeQuestionBatchLLM,
            formatted_system_prompt,
            user_message,
        )
        logger.info(
            f"Batch generation successful: {len(result.node_batches)} node batches returned"
        )
        return result

    except Exception as e:
        logger.error(f"Batch generation failed: {e}")
        return None


# ==================== Conversion to API Schema ====================


def convert_to_question_create(
    generated: GeneratedQuestionLLM,
    node_id: str,
) -> dict:
    """
    Convert a generated question to the format expected by QuestionCreate schema.

    Args:
        generated: The LLM-generated question
        node_id: UUID of the knowledge node (as string)

    Returns:
        Dict matching QuestionCreate schema structure
    """
    details = {
        "explanation": generated.explanation,
        "p_g": 0.25 if generated.question_type == "multiple_choice" else 0.1,
        "p_s": 0.1,
    }

    if generated.question_type == "multiple_choice" and generated.options:
        details["options"] = [opt.text for opt in generated.options]
        details["correct_answer"] = next(
            (i for i, opt in enumerate(generated.options) if opt.is_correct), 0
        )
    elif generated.expected_answers:
        details["expected_answers"] = generated.expected_answers

    return {
        "node_id": node_id,
        "question_type": generated.question_type,
        "text": generated.text,
        "details": details,
        "difficulty": generated.difficulty,
    }


# ==================== Database Integration ====================


async def generate_questions_for_graph(
    graph_id: str,
    questions_per_node: int = 3,
    difficulty_distribution: dict | None = None,
    question_types: list[str] | None = None,
    user_guidance: str = "",
    only_nodes_without_questions: bool = True,
    config: PipelineConfig | None = None,
) -> dict:
    """
    Generate questions for all leaf nodes in a knowledge graph.

    This is the main entry point for batch question generation. It:
    1. Fetches all leaf nodes from the database
    2. Optionally filters to only nodes without existing questions
    3. Generates questions for each node using LLM
    4. Saves generated questions to the database

    Args:
        graph_id: UUID of the knowledge graph (as string)
        questions_per_node: Number of questions per node (default: 3)
        difficulty_distribution: Dict like {"easy": 1, "medium": 1, "hard": 1}
        question_types: List of preferred types
        user_guidance: Additional instructions for the LLM
        only_nodes_without_questions: If True, skip nodes that already have questions
        config: Pipeline configuration

    Returns:
        Dict with generation statistics:
        {
            "nodes_processed": int,
            "nodes_skipped": int,
            "questions_generated": int,
            "questions_saved": int,
            "errors": List[str]
        }

    Example:
        from app.services.generate_questions import generate_questions_for_graph

        result = await generate_questions_for_graph(
            graph_id="550e8400-e29b-41d4-a716-446655440000",
            questions_per_node=5,
            difficulty_distribution={"easy": 2, "medium": 2, "hard": 1},
        )
        print(f"Generated {result['questions_generated']} questions")
    """
    from uuid import UUID as PyUUID

    from app.core.database import db_manager
    from app.crud.knowledge_node import get_nodes_by_graph
    from app.crud.question import bulk_create_questions, get_questions_by_graph

    config = config or PipelineConfig()
    graph_uuid = PyUUID(graph_id) if isinstance(graph_id, str) else graph_id

    stats = {
        "nodes_processed": 0,
        "nodes_skipped": 0,
        "questions_generated": 0,
        "questions_saved": 0,
        "errors": [],
    }

    async with db_manager.get_sql_session() as db_session:
        # Step 1: Fetch all nodes
        all_nodes = await get_nodes_by_graph(db_session, graph_uuid)

        if not all_nodes:
            logger.info("No nodes found in graph")
            return stats

        # Filter nodes if requested
        if only_nodes_without_questions:
            existing_questions = await get_questions_by_graph(db_session, graph_uuid)
            nodes_with_questions = {q.node_id for q in existing_questions}
            target_nodes = [n for n in all_nodes if n.id not in nodes_with_questions]
            logger.info(
                f"Found {len(target_nodes)} nodes without questions (out of {len(all_nodes)} total)"
            )
        else:
            target_nodes = all_nodes
            logger.info(f"Processing all {len(target_nodes)} nodes")
        if not target_nodes:
            logger.info("No nodes to process after filtering")
            return stats

        # Step 2: Generate questions for ALL nodes in ONE batch call
        # Filter out nodes without descriptions
        valid_nodes = [
            {"name": node.node_name, "description": node.description, "id": node.id}
            for node in target_nodes
            if node.description
        ]

        skipped_count = len(target_nodes) - len(valid_nodes)
        if skipped_count > 0:
            logger.warning(f"Skipping {skipped_count} nodes without descriptions")
            stats["nodes_skipped"] += skipped_count

        if not valid_nodes:
            logger.info("No valid nodes to process")
            return stats

        logger.info(
            f"🚀 Batch generating questions for {len(valid_nodes)} nodes in ONE LLM call"
        )

        try:
            # Use batch generation - ONE LLM call for all nodes!
            batch_result = generate_questions_for_nodes_batch(
                nodes=valid_nodes,
                questions_per_node=questions_per_node,
                difficulty_distribution=difficulty_distribution,
                question_types=question_types,
                user_guidance=user_guidance,
                config=config,
            )

            if not batch_result or not batch_result.node_batches:
                logger.error("Batch generation returned no results")
                stats["errors"].append("Batch generation failed - no results returned")
                return stats

            # Create a mapping from node name to node object for quick lookup
            node_map = {node["name"]: node for node in valid_nodes}

            # Process each node's questions from the batch result
            for node_batch in batch_result.node_batches:
                node_name = node_batch.node_name

                # Find the corresponding node
                if node_name not in node_map:
                    logger.warning(
                        f"LLM returned questions for unknown node: {node_name}"
                    )
                    stats["errors"].append(f"Unknown node in batch result: {node_name}")
                    continue

                node_data = node_map[node_name]
                node_id = node_data["id"]

                if not node_batch.questions:
                    logger.warning(f"No questions generated for node: {node_name}")
                    stats["nodes_skipped"] += 1
                    stats["errors"].append(f"No questions generated for: {node_name}")
                    continue

                stats["nodes_processed"] += 1
                stats["questions_generated"] += len(node_batch.questions)

                # Convert to database format
                node_questions_data = []
                for q in node_batch.questions:
                    q_data = convert_to_question_create(q, str(node_id))
                    node_questions_data.append(q_data)

                # Save immediately (Incremental Save)
                if node_questions_data:
                    try:
                        saved = await bulk_create_questions(
                            db_session, graph_uuid, node_questions_data
                        )
                        stats["questions_saved"] += saved
                        logger.info(f"✅ Saved {saved} questions for node: {node_name}")
                    except Exception as e:
                        stats["errors"].append(f"Save error for {node_name}: {e}")
                        logger.error(f"Failed to save questions for {node_name}: {e}")

        except Exception as e:
            logger.error(f"Batch generation failed: {e}")
            stats["errors"].append(f"Batch generation error: {str(e)}")
            return stats

    logger.info(
        f"Generation complete: {stats['nodes_processed']} nodes processed, "
        f"{stats['questions_generated']} questions generated, "
        f"{stats['questions_saved']} saved"
    )

    return stats
