"""
LangChain pipeline for generating quiz questions from knowledge graph nodes.

This pipeline follows the same pattern as generate_graph.py:
- Uses Google Gemini LLM with structured output
- Few-shot examples for consistent formatting
- Retry logic with exponential backoff
- Configurable via PipelineConfig
"""

import logging
import os
from dataclasses import dataclass
from typing import List, Literal, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

# Configuration defaults
DEFAULT_MODEL_NAME = "gemini-3-pro-preview"
DEFAULT_MODEL_TEMPERATURE = 0.7  # Slightly higher for creative question generation
DEFAULT_MAX_RETRY_ATTEMPTS = 3

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
    options: Optional[List[QuestionOptionLLM]] = Field(
        default=None, description="Options for multiple choice (4 options required)"
    )
    # For fill_blank and short_answer
    expected_answers: Optional[List[str]] = Field(
        default=None, description="Acceptable answers for fill_blank/short_answer"
    )
    explanation: str = Field(
        description="Brief explanation of why the answer is correct"
    )


class QuestionBatchLLM(BaseModel):
    """Batch of generated questions for a single knowledge node."""

    questions: List[GeneratedQuestionLLM] = Field(
        description="List of generated questions"
    )


# ==================== Pipeline Configuration ====================


@dataclass
class PipelineConfig:
    """Configuration for the question generation pipeline."""

    model_name: str = DEFAULT_MODEL_NAME
    temperature: float = DEFAULT_MODEL_TEMPERATURE
    max_retry_attempts: int = DEFAULT_MAX_RETRY_ATTEMPTS


class MissingAPIKeyError(Exception):
    """Raised when the Google API key is not configured."""

    pass


# ==================== Prompts ====================

SYSTEM_PROMPT = """
You are an expert Educational Content Creator specializing in generating high-quality quiz questions for adaptive learning systems.

### Your Task:
Generate quiz questions to test a student's understanding of a specific knowledge concept.

### Question Types:
1. **multiple_choice**: 4 options, exactly 1 correct answer
2. **fill_blank**: Complete a sentence/formula with the correct term
3. **short_answer**: Brief response questions (1-3 words or a short phrase)

### Difficulty Levels:
- **easy**: Tests basic recall and recognition
- **medium**: Tests understanding and application
- **hard**: Tests analysis, synthesis, or edge cases

### Quality Guidelines:
1. Questions should be clear, unambiguous, and directly test the concept
2. Avoid trivial or trick questions
3. Multiple choice distractors should be plausible but clearly wrong
4. Each question should have educational value
5. Vary the question types and difficulty as requested
6. Explanations should help students understand why the answer is correct

### Output Requirements:
- Generate exactly the number of questions requested
- Distribute difficulty levels as specified
- Include a mix of question types unless specified otherwise

{user_guidance}
"""

FEW_SHOT_EXAMPLES = [
    (
        "human",
        """
Node Name: Photosynthesis
Node Description: The process by which plants convert light energy, water, and carbon dioxide into glucose and oxygen.

Generate 3 questions (1 easy, 1 medium, 1 hard).
""",
    ),
    (
        "ai",
        """{{
  "questions": [
    {{
      "question_type": "multiple_choice",
      "text": "What are the main products of photosynthesis?",
      "difficulty": "easy",
      "options": [
        {{"text": "Glucose and oxygen", "is_correct": true}},
        {{"text": "Carbon dioxide and water", "is_correct": false}},
        {{"text": "Protein and fat", "is_correct": false}},
        {{"text": "Nitrogen and hydrogen", "is_correct": false}}
      ],
      "expected_answers": null,
      "explanation": "Photosynthesis produces glucose (C6H12O6) as food for the plant and releases oxygen (O2) as a byproduct."
    }},
    {{
      "question_type": "fill_blank",
      "text": "During photosynthesis, plants absorb _____ from the air and release oxygen.",
      "difficulty": "medium",
      "options": null,
      "expected_answers": ["carbon dioxide", "CO2"],
      "explanation": "Plants take in carbon dioxide (CO2) through their stomata, which is then used with water and light energy to produce glucose."
    }},
    {{
      "question_type": "short_answer",
      "text": "Why can't photosynthesis occur in complete darkness?",
      "difficulty": "hard",
      "options": null,
      "expected_answers": ["Light energy is required", "No light energy", "Light is needed to power the reaction"],
      "explanation": "Photosynthesis requires light energy to drive the light-dependent reactions that split water molecules and produce ATP and NADPH for the Calvin cycle."
    }}
  ]
}}""",
    ),
    (
        "human",
        """
Node Name: Newton's Second Law
Node Description: The acceleration of an object is directly proportional to the net force acting on it and inversely proportional to its mass. Expressed as F = ma.

Generate 2 questions (1 medium, 1 hard).
""",
    ),
    (
        "ai",
        """{{
  "questions": [
    {{
      "question_type": "multiple_choice",
      "text": "A 10 kg object experiences a net force of 50 N. What is its acceleration?",
      "difficulty": "medium",
      "options": [
        {{"text": "5 m/s²", "is_correct": true}},
        {{"text": "500 m/s²", "is_correct": false}},
        {{"text": "0.2 m/s²", "is_correct": false}},
        {{"text": "60 m/s²", "is_correct": false}}
      ],
      "expected_answers": null,
      "explanation": "Using F = ma, we get a = F/m = 50 N / 10 kg = 5 m/s²."
    }},
    {{
      "question_type": "short_answer",
      "text": "If you double the mass of an object while keeping the force constant, what happens to the acceleration?",
      "difficulty": "hard",
      "options": null,
      "expected_answers": ["It halves", "Halved", "Reduced by half", "Becomes half"],
      "explanation": "Since a = F/m, doubling the mass (m → 2m) while keeping F constant results in a → F/(2m) = a/2. The acceleration is halved."
    }}
  ]
}}""",
    ),
]


# ==================== LLM Initialization ====================


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
        google_api_key=api_key,
    )
    return llm.with_structured_output(QuestionBatchLLM)


# ==================== Question Generation ====================


def _create_generate_with_retry(max_attempts: int):
    """Factory function to create generate function with configurable retry."""

    @retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def _generate(
        llm_struct,
        node_name: str,
        node_description: str,
        num_questions: int = 3,
        difficulty_distribution: Optional[dict] = None,
        question_types: Optional[List[str]] = None,
        user_guidance: str = "",
    ) -> QuestionBatchLLM:
        """Generate questions for a single knowledge node."""

        # Build difficulty instruction
        if difficulty_distribution:
            diff_str = ", ".join(
                f"{count} {level}" for level, count in difficulty_distribution.items()
            )
        else:
            # Default: balanced distribution
            easy = num_questions // 3
            hard = num_questions // 3
            medium = num_questions - easy - hard
            diff_str = f"{easy} easy, {medium} medium, {hard} hard"

        # Build question type instruction
        type_str = ""
        if question_types:
            type_str = f"\nPreferred question types: {', '.join(question_types)}"

        formatted_system_prompt = SYSTEM_PROMPT.format(
            user_guidance=(
                f"### Extra Instructions:\n{user_guidance}" if user_guidance else ""
            )
        )

        user_message = f"""
Node Name: {node_name}
Node Description: {node_description}

Generate {num_questions} questions ({diff_str}).{type_str}
"""

        prompt_messages = [("system", formatted_system_prompt)]
        prompt_messages.extend(FEW_SHOT_EXAMPLES)
        prompt_messages.append(("human", "{user_input}"))

        prompt = ChatPromptTemplate.from_messages(prompt_messages)
        chain = prompt | llm_struct
        return chain.invoke({"user_input": user_message})

    return _generate


def generate_questions_for_node(
    node_name: str,
    node_description: str,
    num_questions: int = 3,
    difficulty_distribution: Optional[dict] = None,
    question_types: Optional[List[str]] = None,
    user_guidance: str = "",
    config: Optional[PipelineConfig] = None,
) -> Optional[QuestionBatchLLM]:
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

    llm_struct = _get_llm(config)
    generate = _create_generate_with_retry(config.max_retry_attempts)

    logger.info(f"Generating {num_questions} questions for node: {node_name}")

    try:
        result = generate(
            llm_struct,
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


def generate_questions_for_nodes(
    nodes: List[dict],
    questions_per_node: int = 3,
    difficulty_distribution: Optional[dict] = None,
    question_types: Optional[List[str]] = None,
    user_guidance: str = "",
    config: Optional[PipelineConfig] = None,
) -> dict[str, QuestionBatchLLM]:
    """
    Generate questions for multiple knowledge nodes.

    Args:
        nodes: List of dicts with 'name' and 'description' keys
        questions_per_node: Number of questions per node
        difficulty_distribution: Dict like {"easy": 1, "medium": 1, "hard": 1}
        question_types: List of preferred types
        user_guidance: Additional instructions
        config: Pipeline configuration

    Returns:
        Dict mapping node names to their generated questions

    Example:
        nodes = [
            {"name": "Photosynthesis", "description": "Process by which..."},
            {"name": "Cellular Respiration", "description": "Process of..."}
        ]
        results = generate_questions_for_nodes(nodes, questions_per_node=5)
    """
    config = config or PipelineConfig()
    results = {}

    for i, node in enumerate(nodes, 1):
        name = node.get("name", "")
        description = node.get("description", "")

        if not name or not description:
            logger.warning(f"Skipping node {i}: missing name or description")
            continue

        logger.info(f"Processing node {i}/{len(nodes)}: {name}")

        questions = generate_questions_for_node(
            node_name=name,
            node_description=description,
            num_questions=questions_per_node,
            difficulty_distribution=difficulty_distribution,
            question_types=question_types,
            user_guidance=user_guidance,
            config=config,
        )

        if questions:
            results[name] = questions
        else:
            logger.warning(f"Failed to generate questions for: {name}")

    logger.info(f"Completed: Generated questions for {len(results)}/{len(nodes)} nodes")
    return results


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
    difficulty_distribution: Optional[dict] = None,
    question_types: Optional[List[str]] = None,
    user_guidance: str = "",
    only_nodes_without_questions: bool = True,
    config: Optional[PipelineConfig] = None,
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
    from app.crud.knowledge_graph import (
        bulk_create_questions,
        get_leaf_nodes_by_graph,
        get_leaf_nodes_without_questions,
    )

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
        # Step 1: Fetch leaf nodes
        if only_nodes_without_questions:
            leaf_nodes = await get_leaf_nodes_without_questions(db_session, graph_uuid)
            logger.info(f"Found {len(leaf_nodes)} leaf nodes without questions")
        else:
            leaf_nodes = await get_leaf_nodes_by_graph(db_session, graph_uuid)
            logger.info(f"Found {len(leaf_nodes)} total leaf nodes")

        if not leaf_nodes:
            logger.info("No leaf nodes to process")
            return stats

        # Step 2: Generate questions for each node
        all_questions_data = []

        for i, node in enumerate(leaf_nodes, 1):
            if not node.description:
                logger.warning(f"Skipping node '{node.node_name}': no description")
                stats["nodes_skipped"] += 1
                continue

            logger.info(
                f"[{i}/{len(leaf_nodes)}] Generating questions for: {node.node_name}"
            )

            try:
                result = generate_questions_for_node(
                    node_name=node.node_name,
                    node_description=node.description,
                    num_questions=questions_per_node,
                    difficulty_distribution=difficulty_distribution,
                    question_types=question_types,
                    user_guidance=user_guidance,
                    config=config,
                )

                if result and result.questions:
                    stats["nodes_processed"] += 1
                    stats["questions_generated"] += len(result.questions)

                    # Convert to database format
                    for q in result.questions:
                        q_data = convert_to_question_create(q, str(node.id))
                        all_questions_data.append(q_data)
                else:
                    stats["nodes_skipped"] += 1
                    stats["errors"].append(
                        f"No questions generated for: {node.node_name}"
                    )

            except Exception as e:
                stats["nodes_skipped"] += 1
                stats["errors"].append(f"Error for {node.node_name}: {str(e)}")
                logger.error(f"Failed to generate questions for {node.node_name}: {e}")

        # Step 3: Bulk save questions to database
        if all_questions_data:
            try:
                saved_count = await bulk_create_questions(
                    db_session, graph_uuid, all_questions_data
                )
                stats["questions_saved"] = saved_count
                logger.info(f"Saved {saved_count} questions to database")
            except Exception as e:
                stats["errors"].append(f"Database save error: {str(e)}")
                logger.error(f"Failed to save questions: {e}")

    logger.info(
        f"Generation complete: {stats['nodes_processed']} nodes processed, "
        f"{stats['questions_generated']} questions generated, "
        f"{stats['questions_saved']} saved"
    )

    return stats
