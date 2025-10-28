"""
Bulk import handlers for CSV-based data import.

These handlers process CSV files uploaded via the API endpoints and create
Neo4j nodes and relationships in batch.
"""

import asyncio
import csv
import json
import os
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd
from neomodel import DoesNotExist

from app.worker.config import WorkerContext, register_handler
from app.helper.course_helper import parse_course_id
from app.schemas.knowledge_node import RelationType
from app.schemas.questions import QuestionDifficulty
import app.models.neo4j_model as neo


class BulkImportError(Exception):
    """Base exception for bulk import errors"""
    pass


def validate_csv_columns(df: pd.DataFrame, required_columns: List[str], file_type: str):
    """Validate that CSV has all required columns"""
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise BulkImportError(
            f"{file_type} CSV missing required columns: {missing}"
        )


@register_handler("handle_bulk_import_nodes")
async def handle_bulk_import_nodes(payload: dict, ctx: WorkerContext) -> dict:
    """
    Bulk import knowledge nodes from CSV file.

    CSV Format:
        node_id,name,description,course_id
        node1,Node Name,Description text,g10_phys

    Args:
        payload: {
            "file_path": "/path/to/nodes.csv",
            "requested_by": "admin@example.com"
        }
        ctx: Worker context with database connections

    Returns:
        {
            "status": "completed",
            "total_rows": 100,
            "successful": 95,
            "failed": 5,
            "errors": [{"row": 3, "node_id": "xyz", "error": "..."}]
        }
    """
    file_path = payload.get("file_path")
    requested_by = payload.get("requested_by", "unknown")

    print(f"📥 Starting bulk import of knowledge nodes (requested by {requested_by})")
    print(f"📄 Reading file: {file_path}")

    if not file_path or not Path(file_path).exists():
        raise BulkImportError(f"File not found: {file_path}")

    try:
        # Read CSV
        df = pd.read_csv(file_path)
        total_rows = len(df)
        print(f"📊 Found {total_rows} nodes to import")

        # Validate columns
        required_columns = ["node_id", "name", "description", "course_id"]
        validate_csv_columns(df, required_columns, "nodes")

        # Process each row
        successful = 0
        failed = 0
        errors = []

        async with ctx.neo4j_scoped_connection():
            for idx, row in df.iterrows():
                row_num = idx + 2  # +2 because: 0-indexed + header row

                try:
                    await asyncio.to_thread(
                        _create_node_from_row,
                        row,
                        row_num
                    )
                    successful += 1
                    print(f"✅ [{successful}/{total_rows}] Created node: {row['node_id']}")

                except Exception as e:
                    failed += 1
                    error_msg = str(e)
                    errors.append({
                        "row": row_num,
                        "node_id": row.get("node_id", "unknown"),
                        "error": error_msg
                    })
                    print(f"❌ [{successful + failed}/{total_rows}] Failed to create node {row.get('node_id')}: {error_msg}")

        # Summary
        print(f"\n📈 Bulk import completed:")
        print(f"   Total: {total_rows}")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")

        result = {
            "status": "completed",
            "total_rows": total_rows,
            "successful": successful,
            "failed": failed,
            "errors": errors
        }

        return result

    finally:
        # Clean up temporary file
        if file_path and Path(file_path).exists():
            os.remove(file_path)
            print(f"🗑️  Cleaned up temporary file: {file_path}")


def _create_node_from_row(row: pd.Series, row_num: int):
    """
    Synchronous function to create a single knowledge node from CSV row.

    Called via asyncio.to_thread() from the async handler.
    """
    node_id = str(row["node_id"]).strip()
    name = str(row["name"]).strip()
    description = str(row["description"]).strip()
    course_id = str(row["course_id"]).strip()

    # Validate course exists
    try:
        course = neo.Course.nodes.get(course_id=course_id)
    except DoesNotExist:
        raise ValueError(f"Course {course_id} does not exist")

    # Check if node already exists (idempotent operation)
    existing_node = neo.KnowledgeNode.nodes.get_or_none(node_id=node_id)

    if existing_node:
        # Update existing node
        existing_node.node_name = name
        existing_node.description = description
        existing_node.save()

        # Update course relationship if different
        current_course = existing_node.course.single()
        if current_course.course_id != course_id:
            existing_node.course.disconnect_all()
            existing_node.course.connect(course)
    else:
        # Create new node
        new_node = neo.KnowledgeNode(
            node_id=node_id,
            node_name=name,
            description=description
        ).save()
        new_node.course.connect(course)


@register_handler("handle_bulk_import_question")
async def handle_bulk_import_question(payload: dict, ctx: WorkerContext) -> dict:
    """
    Bulk import multiple choice questions from CSV file.

    CSV Format:
        question_id,text,difficulty,knowledge_node_id,options,correct_answer
        q1,"What is 2+2?",easy,node1,"[""2"",""3"",""4"",""5""]",2

    Args:
        payload: {
            "file_path": "/path/to/questions.csv",
            "requested_by": "admin@example.com"
        }
        ctx: Worker context with database connections

    Returns:
        {
            "status": "completed",
            "total_rows": 100,
            "successful": 95,
            "failed": 5,
            "errors": [{"row": 3, "question_id": "q3", "error": "..."}]
        }
    """
    file_path = payload.get("file_path")
    requested_by = payload.get("requested_by", "unknown")

    print(f"📥 Starting bulk import of questions (requested by {requested_by})")
    print(f"📄 Reading file: {file_path}")

    if not file_path or not Path(file_path).exists():
        raise BulkImportError(f"File not found: {file_path}")

    try:
        # Read CSV
        df = pd.read_csv(file_path)
        total_rows = len(df)
        print(f"📊 Found {total_rows} questions to import")

        # Validate columns
        required_columns = ["question_id", "text", "difficulty",
                          "knowledge_node_id", "options", "correct_answer"]
        validate_csv_columns(df, required_columns, "questions")

        # Process each row
        successful = 0
        failed = 0
        errors = []

        async with ctx.neo4j_scoped_connection():
            for idx, row in df.iterrows():
                row_num = idx + 2  # +2 because: 0-indexed + header row

                try:
                    await asyncio.to_thread(
                        _create_question_from_row,
                        row,
                        row_num
                    )
                    successful += 1
                    print(f"✅ [{successful}/{total_rows}] Created question: {row['question_id']}")

                except Exception as e:
                    failed += 1
                    error_msg = str(e)
                    errors.append({
                        "row": row_num,
                        "question_id": row.get("question_id", "unknown"),
                        "error": error_msg
                    })
                    print(f"❌ [{successful + failed}/{total_rows}] Failed to create question {row.get('question_id')}: {error_msg}")

        # Summary
        print(f"\n📈 Bulk import completed:")
        print(f"   Total: {total_rows}")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")

        result = {
            "status": "completed",
            "total_rows": total_rows,
            "successful": successful,
            "failed": failed,
            "errors": errors
        }

        return result

    finally:
        # Clean up temporary file
        if file_path and Path(file_path).exists():
            os.remove(file_path)
            print(f"🗑️  Cleaned up temporary file: {file_path}")


def _create_question_from_row(row: pd.Series, row_num: int):
    """
    Synchronous function to create a single multiple choice question from CSV row.

    Called via asyncio.to_thread() from the async handler.
    """
    question_id = str(row["question_id"]).strip()
    text = str(row["text"]).strip()
    difficulty = str(row["difficulty"]).strip().lower()
    knowledge_node_id = str(row["knowledge_node_id"]).strip()
    options_str = str(row["options"]).strip()
    correct_answer = int(row["correct_answer"])

    # Validate difficulty
    valid_difficulties = {d.value for d in QuestionDifficulty}
    if difficulty not in valid_difficulties:
        raise ValueError(
            f"Invalid difficulty '{difficulty}'. Must be one of: {valid_difficulties}"
        )

    # Parse options JSON
    try:
        options = json.loads(options_str)
        if not isinstance(options, list):
            raise ValueError("Options must be a JSON array")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in options field: {e}")

    # Validate correct_answer index
    if not (0 <= correct_answer < len(options)):
        raise ValueError(
            f"correct_answer ({correct_answer}) must be between 0 and {len(options)-1}"
        )

    # Verify knowledge node exists
    try:
        knowledge_node = neo.KnowledgeNode.nodes.get(node_id=knowledge_node_id)
    except DoesNotExist:
        raise ValueError(
            f"Knowledge node '{knowledge_node_id}' does not exist. "
            "Please import nodes before importing questions."
        )

    # Check if question already exists
    existing_question = neo.MultipleChoice.nodes.get_or_none(question_id=question_id)

    if existing_question:
        # Update existing question
        existing_question.text = text
        existing_question.difficulty = difficulty
        existing_question.options = options
        existing_question.correct_answer = correct_answer
        existing_question.save()

        # Update knowledge node relationship if different
        current_node = existing_question.knowledge_node.single()
        if current_node.node_id != knowledge_node_id:
            # Use reconnect() for cardinality=One relationships
            existing_question.knowledge_node.reconnect(current_node, knowledge_node)
    else:
        # Create new question
        new_question = neo.MultipleChoice(
            question_id=question_id,
            text=text,
            difficulty=difficulty,
            options=options,
            correct_answer=correct_answer
        ).save()
        new_question.knowledge_node.connect(knowledge_node)


@register_handler("handle_bulk_import_relations")
async def handle_bulk_import_relations(payload: dict, ctx: WorkerContext) -> dict:
    """
    Bulk import knowledge node relationships from CSV file.

    CSV Format:
        from_node_id,to_node_id,relationship_type
        node1,node2,HAS_PREREQUISITES
        node1,node3,HAS_SUBTOPIC

    Args:
        payload: {
            "file_path": "/path/to/relationships.csv",
            "requested_by": "admin@example.com"
        }
        ctx: Worker context with database connections

    Returns:
        {
            "status": "completed",
            "total_rows": 100,
            "successful": 95,
            "failed": 5,
            "errors": [{"row": 3, "error": "..."}]
        }
    """
    file_path = payload.get("file_path")
    requested_by = payload.get("requested_by", "unknown")

    print(f"📥 Starting bulk import of relationships (requested by {requested_by})")
    print(f"📄 Reading file: {file_path}")

    if not file_path or not Path(file_path).exists():
        raise BulkImportError(f"File not found: {file_path}")

    try:
        # Read CSV
        df = pd.read_csv(file_path)
        total_rows = len(df)
        print(f"📊 Found {total_rows} relationships to import")

        # Validate columns
        required_columns = ["from_node_id", "to_node_id", "relationship_type"]
        validate_csv_columns(df, required_columns, "relationships")

        # Process each row
        successful = 0
        failed = 0
        errors = []

        async with ctx.neo4j_scoped_connection():
            for idx, row in df.iterrows():
                row_num = idx + 2  # +2 because: 0-indexed + header row

                try:
                    await asyncio.to_thread(
                        _create_relation_from_row,
                        row,
                        row_num
                    )
                    successful += 1
                    print(f"✅ [{successful}/{total_rows}] Created relation: {row['from_node_id']} -> {row['to_node_id']} ({row['relationship_type']})")

                except Exception as e:
                    failed += 1
                    error_msg = str(e)
                    errors.append({
                        "row": row_num,
                        "from_node_id": row.get("from_node_id", "unknown"),
                        "to_node_id": row.get("to_node_id", "unknown"),
                        "relationship_type": row.get("relationship_type", "unknown"),
                        "error": error_msg
                    })
                    print(f"❌ [{successful + failed}/{total_rows}] Failed to create relation: {error_msg}")

        # Summary
        print(f"\n📈 Bulk import completed:")
        print(f"   Total: {total_rows}")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")

        result = {
            "status": "completed",
            "total_rows": total_rows,
            "successful": successful,
            "failed": failed,
            "errors": errors
        }

        return result

    finally:
        # Clean up temporary file
        if file_path and Path(file_path).exists():
            os.remove(file_path)
            print(f"🗑️  Cleaned up temporary file: {file_path}")


def _create_relation_from_row(row: pd.Series, row_num: int):
    """
    Synchronous function to create a single relationship from CSV row.

    Called via asyncio.to_thread() from the async handler.
    """
    from_node_id = str(row["from_node_id"]).strip()
    to_node_id = str(row["to_node_id"]).strip()
    relationship_type = str(row["relationship_type"]).strip()

    # Validate relationship type
    valid_types = {rt.value for rt in RelationType}
    if relationship_type not in valid_types:
        raise ValueError(
            f"Invalid relationship_type '{relationship_type}'. "
            f"Must be one of: {valid_types}"
        )

    # Fetch both nodes
    try:
        source_node = neo.KnowledgeNode.nodes.get(node_id=from_node_id)
    except DoesNotExist:
        raise ValueError(f"Source node '{from_node_id}' does not exist")

    try:
        target_node = neo.KnowledgeNode.nodes.get(node_id=to_node_id)
    except DoesNotExist:
        raise ValueError(f"Target node '{to_node_id}' does not exist")

    # Create relationship based on type
    # Check if relationship already exists to avoid duplicates
    if relationship_type == RelationType.HAS_PREREQUISITES.value:
        if not source_node.prerequisites.is_connected(target_node):
            source_node.prerequisites.connect(target_node)

    elif relationship_type == RelationType.HAS_SUBTOPIC.value:
        if not source_node.subtopic.is_connected(target_node):
            source_node.subtopic.connect(target_node)

    elif relationship_type == RelationType.IS_EXAMPLE_OF.value:
        if not source_node.concept_this_is_example_of.is_connected(target_node):
            source_node.concept_this_is_example_of.connect(target_node)

    # If relationship already exists, it's idempotent - no error
