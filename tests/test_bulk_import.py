"""
Unit tests for bulk import handlers in app/worker/bulk_import_handlers.py

This module tests the bulk import functionality including:
- handle_bulk_import_nodes()
- handle_bulk_import_question()
- handle_bulk_import_relations()
- CSV validation and error handling
"""

# import asyncio
# import json
# from pathlib import Path
# from tempfile import NamedTemporaryFile
# from typing import Any, AsyncGenerator
#
# import pandas as pd
# import pytest
# import pytest_asyncio
#
# import app.models.neo4j_model as neo
# from app.core.database import DatabaseManager
# from app.worker.bulk_import_handlers import (
#     BulkImportError,
#     handle_bulk_import_nodes,
#     handle_bulk_import_question,
#     handle_bulk_import_relations,
#     validate_csv_columns,
# )
# from app.worker.config import WorkerContext
#
# # Test constants
# TEST_COURSE_ID = "g10_phys"
# TEST_COURSE_NAME = "Grade 10 Physics"
#
#
# # =============================================================================
# # Fixtures
# # =============================================================================
#
#
# @pytest_asyncio.fixture(scope="function")
# async def test_course_in_neo4j(
#     test_db_manager: DatabaseManager,
# ) -> AsyncGenerator[neo.Course, Any]:
#     """Create a test course in Neo4j for bulk import tests."""
#     course = neo.Course(
#         course_id=TEST_COURSE_ID,
#         course_name=TEST_COURSE_NAME,
#     )
#
#     async with test_db_manager.neo4j_scoped_connection():
#         await asyncio.to_thread(course.save)
#
#     yield course
#
#
# @pytest_asyncio.fixture(scope="function")
# async def worker_ctx(test_db_manager: DatabaseManager) -> WorkerContext:
#     """Create a WorkerContext for testing handlers."""
#     return WorkerContext(db_mng=test_db_manager)
#
#
# def create_temp_csv(content: str) -> Path:
#     """Helper to create a temporary CSV file with given content."""
#     temp_file = NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
#     temp_file.write(content)
#     temp_file.flush()
#     temp_file.close()
#     return Path(temp_file.name)
#
#
# # =============================================================================
# # Test CSV Validation Helper
# # =============================================================================
# # Note: CSV validation is tested implicitly through the import tests below
#
#
# # =============================================================================
# # Test handle_bulk_import_nodes
# # =============================================================================
#
#
# @pytest.mark.asyncio
# class TestBulkImportNodes:
#     """Test suite for bulk importing knowledge nodes."""
#
#     async def test_import_nodes_success(
#         self,
#         worker_ctx: WorkerContext,
#         test_course_in_neo4j: neo.Course,
#     ):
#         """Test successful bulk import of knowledge nodes."""
#         csv_content = f"""node_id,name,description,course_id
# node1,Node One,First node,{TEST_COURSE_ID}
# node2,Node Two,Second node,{TEST_COURSE_ID}
# node3,Node Three,Third node,{TEST_COURSE_ID}
# """
#         csv_file = create_temp_csv(csv_content)
#
#         try:
#             payload = {
#                 "file_path": str(csv_file),
#                 "requested_by": "test@example.com"
#             }
#
#             result = await handle_bulk_import_nodes(payload, worker_ctx)
#
#             assert result["status"] == "completed"
#             assert result["total_rows"] == 3
#             assert result["successful"] == 3
#             assert result["failed"] == 0
#             assert result["errors"] == []
#
#             # Verify nodes were created
#             async with worker_ctx.neo4j_scoped_connection():
#                 node1 = await asyncio.to_thread(
#                     neo.KnowledgeNode.nodes.get_or_none,
#                     node_id="node1"
#                 )
#                 node2 = await asyncio.to_thread(
#                     neo.KnowledgeNode.nodes.get_or_none,
#                     node_id="node2"
#                 )
#
#                 assert node1 is not None
#                 assert node1.node_name == "Node One"
#                 assert node1.description == "First node"
#
#                 assert node2 is not None
#                 assert node2.node_name == "Node Two"
#
#         finally:
#             # File should be auto-deleted by handler
#             assert not csv_file.exists()
#
#     async def test_import_nodes_idempotent(
#         self,
#         worker_ctx: WorkerContext,
#         test_course_in_neo4j: neo.Course,
#     ):
#         """Test that importing same node twice updates instead of failing."""
#         # First import
#         csv_content1 = f"""node_id,name,description,course_id
# node_update,Original Name,Original description,{TEST_COURSE_ID}
# """
#         csv_file1 = create_temp_csv(csv_content1)
#
#         payload1 = {
#             "file_path": str(csv_file1),
#             "requested_by": "test@example.com"
#         }
#
#         result1 = await handle_bulk_import_nodes(payload1, worker_ctx)
#         assert result1["successful"] == 1
#
#         # Second import with updated data
#         csv_content2 = f"""node_id,name,description,course_id
# node_update,Updated Name,Updated description,{TEST_COURSE_ID}
# """
#         csv_file2 = create_temp_csv(csv_content2)
#
#         payload2 = {
#             "file_path": str(csv_file2),
#             "requested_by": "test@example.com"
#         }
#
#         result2 = await handle_bulk_import_nodes(payload2, worker_ctx)
#         assert result2["successful"] == 1
#
#         # Verify node was updated
#         async with worker_ctx.neo4j_scoped_connection():
#             node = await asyncio.to_thread(
#                 neo.KnowledgeNode.nodes.get,
#                 node_id="node_update"
#             )
#             assert node.node_name == "Updated Name"
#             assert node.description == "Updated description"
#
#     async def test_import_nodes_invalid_course(
#         self,
#         worker_ctx: WorkerContext,
#         test_course_in_neo4j: neo.Course,
#     ):
#         """Test import fails gracefully when course doesn't exist."""
#         csv_content = f"""node_id,name,description,course_id
# node1,Node One,First node,{TEST_COURSE_ID}
# node2,Node Two,Second node,nonexistent_course
# node3,Node Three,Third node,{TEST_COURSE_ID}
# """
#         csv_file = create_temp_csv(csv_content)
#
#         payload = {
#             "file_path": str(csv_file),
#             "requested_by": "test@example.com"
#         }
#
#         result = await handle_bulk_import_nodes(payload, worker_ctx)
#
#         assert result["status"] == "completed"
#         assert result["total_rows"] == 3
#         assert result["successful"] == 2  # node1 and node3
#         assert result["failed"] == 1  # node2
#         assert len(result["errors"]) == 1
#         assert result["errors"][0]["node_id"] == "node2"
#         assert "nonexistent_course" in result["errors"][0]["error"]
#
#     async def test_import_nodes_missing_columns(
#         self,
#         worker_ctx: WorkerContext,
#         test_course_in_neo4j: neo.Course,
#     ):
#         """Test import fails when CSV has missing columns."""
#         csv_content = """node_id,name,course_id
# node1,Node One,g10_phys
# """
#         csv_file = create_temp_csv(csv_content)
#
#         payload = {
#             "file_path": str(csv_file),
#             "requested_by": "test@example.com"
#         }
#
#         with pytest.raises(BulkImportError) as exc_info:
#             await handle_bulk_import_nodes(payload, worker_ctx)
#
#         assert "missing required columns" in str(exc_info.value)
#         assert "description" in str(exc_info.value)
#
#         # File should still be cleaned up
#         assert not csv_file.exists()
#
#     async def test_import_nodes_file_not_found(
#         self,
#         worker_ctx: WorkerContext,
#     ):
#         """Test import fails when file doesn't exist."""
#         payload = {
#             "file_path": "/nonexistent/file.csv",
#             "requested_by": "test@example.com"
#         }
#
#         with pytest.raises(BulkImportError) as exc_info:
#             await handle_bulk_import_nodes(payload, worker_ctx)
#
#         assert "File not found" in str(exc_info.value)
#
#     async def test_import_nodes_empty_csv(
#         self,
#         worker_ctx: WorkerContext,
#         test_course_in_neo4j: neo.Course,
#     ):
#         """Test import handles empty CSV gracefully."""
#         csv_content = """node_id,name,description,course_id
# """
#         csv_file = create_temp_csv(csv_content)
#
#         payload = {
#             "file_path": str(csv_file),
#             "requested_by": "test@example.com"
#         }
#
#         result = await handle_bulk_import_nodes(payload, worker_ctx)
#
#         assert result["status"] == "completed"
#         assert result["total_rows"] == 0
#         assert result["successful"] == 0
#         assert result["failed"] == 0
#
#
# # =============================================================================
# # Test handle_bulk_import_question
# # =============================================================================
#
#
# @pytest.mark.asyncio
# class TestBulkImportQuestions:
#     """Test suite for bulk importing questions."""
#
#     @pytest_asyncio.fixture(scope="function")
#     async def test_nodes_in_neo4j(
#         self,
#         worker_ctx: WorkerContext,
#         test_course_in_neo4j: neo.Course,
#     ) -> AsyncGenerator[tuple[neo.KnowledgeNode, neo.KnowledgeNode], Any]:
#         """Create test knowledge nodes for question tests."""
#         node1 = neo.KnowledgeNode(
#             node_id="test_node_1",
#             node_name="Test Node 1",
#             description="Test node for questions"
#         )
#         node2 = neo.KnowledgeNode(
#             node_id="test_node_2",
#             node_name="Test Node 2",
#             description="Another test node"
#         )
#
#         async with worker_ctx.neo4j_scoped_connection():
#             await asyncio.to_thread(node1.save)
#             await asyncio.to_thread(node2.save)
#             await asyncio.to_thread(node1.course.connect, test_course_in_neo4j)
#             await asyncio.to_thread(node2.course.connect, test_course_in_neo4j)
#
#         yield node1, node2
#
#     async def test_import_questions_success(
#         self,
#         worker_ctx: WorkerContext,
#         test_nodes_in_neo4j: tuple[neo.KnowledgeNode, neo.KnowledgeNode],
#     ):
#         """Test successful bulk import of multiple choice questions."""
#         csv_content = """question_id,text,difficulty,knowledge_node_id,options,correct_answer
# q1,What is 2+2?,easy,test_node_1,"[""2"",""3"",""4"",""5""]",2
# q2,What is Python?,medium,test_node_2,"[""Language"",""Snake"",""Both"",""Neither""]",2
# q3,Hard question?,hard,test_node_1,"[""A"",""B"",""C""]",0
# """
#         csv_file = create_temp_csv(csv_content)
#
#         payload = {
#             "file_path": str(csv_file),
#             "requested_by": "test@example.com"
#         }
#
#         result = await handle_bulk_import_question(payload, worker_ctx)
#
#         assert result["status"] == "completed"
#         assert result["total_rows"] == 3
#         assert result["successful"] == 3
#         assert result["failed"] == 0
#         assert result["errors"] == []
#
#         # Verify questions were created
#         async with worker_ctx.neo4j_scoped_connection():
#             q1 = await asyncio.to_thread(
#                 neo.MultipleChoice.nodes.get_or_none,
#                 question_id="q1"
#             )
#             assert q1 is not None
#             assert q1.text == "What is 2+2?"
#             assert q1.difficulty == "easy"
#             assert q1.options == ["2", "3", "4", "5"]
#             assert q1.correct_answer == 2
#
#             # Verify relationship to knowledge node
#             kn = await asyncio.to_thread(q1.knowledge_node.single)
#             assert kn.node_id == "test_node_1"
#
#     async def test_import_questions_invalid_difficulty(
#         self,
#         worker_ctx: WorkerContext,
#         test_nodes_in_neo4j: tuple[neo.KnowledgeNode, neo.KnowledgeNode],
#     ):
#         """Test import fails gracefully with invalid difficulty."""
#         csv_content = """question_id,text,difficulty,knowledge_node_id,options,correct_answer
# q1,Valid question,easy,test_node_1,"[""A"",""B""]",0
# q2,Invalid difficulty,super_hard,test_node_1,"[""A"",""B""]",0
# q3,Another valid,medium,test_node_1,"[""A"",""B""]",1
# """
#         csv_file = create_temp_csv(csv_content)
#
#         payload = {
#             "file_path": str(csv_file),
#             "requested_by": "test@example.com"
#         }
#
#         result = await handle_bulk_import_question(payload, worker_ctx)
#
#         assert result["status"] == "completed"
#         assert result["total_rows"] == 3
#         assert result["successful"] == 2
#         assert result["failed"] == 1
#         assert len(result["errors"]) == 1
#         assert result["errors"][0]["question_id"] == "q2"
#         assert "super_hard" in result["errors"][0]["error"]
#
#     async def test_import_questions_invalid_json_options(
#         self,
#         worker_ctx: WorkerContext,
#         test_nodes_in_neo4j: tuple[neo.KnowledgeNode, neo.KnowledgeNode],
#     ):
#         """Test import fails gracefully with invalid JSON in options."""
#         csv_content = """question_id,text,difficulty,knowledge_node_id,options,correct_answer
# q1,Good question,easy,test_node_1,"[""A"",""B""]",0
# q2,Bad JSON,easy,test_node_1,"[A,B",0
# """
#         csv_file = create_temp_csv(csv_content)
#
#         payload = {
#             "file_path": str(csv_file),
#             "requested_by": "test@example.com"
#         }
#
#         result = await handle_bulk_import_question(payload, worker_ctx)
#
#         assert result["status"] == "completed"
#         assert result["total_rows"] == 2
#         assert result["successful"] == 1
#         assert result["failed"] == 1
#         assert "Invalid JSON" in result["errors"][0]["error"]
#
#     async def test_import_questions_invalid_correct_answer_index(
#         self,
#         worker_ctx: WorkerContext,
#         test_nodes_in_neo4j: tuple[neo.KnowledgeNode, neo.KnowledgeNode],
#     ):
#         """Test import fails gracefully with out-of-range correct_answer."""
#         csv_content = """question_id,text,difficulty,knowledge_node_id,options,correct_answer
# q1,Valid question,easy,test_node_1,"[""A"",""B"",""C""]",1
# q2,Invalid index,easy,test_node_1,"[""A"",""B""]",5
# """
#         csv_file = create_temp_csv(csv_content)
#
#         payload = {
#             "file_path": str(csv_file),
#             "requested_by": "test@example.com"
#         }
#
#         result = await handle_bulk_import_question(payload, worker_ctx)
#
#         assert result["status"] == "completed"
#         assert result["successful"] == 1
#         assert result["failed"] == 1
#         assert "correct_answer" in result["errors"][0]["error"]
#
#     async def test_import_questions_nonexistent_node(
#         self,
#         worker_ctx: WorkerContext,
#         test_nodes_in_neo4j: tuple[neo.KnowledgeNode, neo.KnowledgeNode],
#     ):
#         """Test import fails gracefully when knowledge node doesn't exist."""
#         csv_content = """question_id,text,difficulty,knowledge_node_id,options,correct_answer
# q1,Valid question,easy,test_node_1,"[""A"",""B""]",0
# q2,Nonexistent node,easy,nonexistent_node,"[""A"",""B""]",0
# """
#         csv_file = create_temp_csv(csv_content)
#
#         payload = {
#             "file_path": str(csv_file),
#             "requested_by": "test@example.com"
#         }
#
#         result = await handle_bulk_import_question(payload, worker_ctx)
#
#         assert result["status"] == "completed"
#         assert result["successful"] == 1
#         assert result["failed"] == 1
#         assert "nonexistent_node" in result["errors"][0]["error"]
#
#     async def test_import_questions_idempotent(
#         self,
#         worker_ctx: WorkerContext,
#         test_nodes_in_neo4j: tuple[neo.KnowledgeNode, neo.KnowledgeNode],
#     ):
#         """Test that importing same question twice updates instead of failing."""
#         # First import
#         csv_content1 = """question_id,text,difficulty,knowledge_node_id,options,correct_answer
# q_update,Original question,easy,test_node_1,"[""A"",""B""]",0
# """
#         csv_file1 = create_temp_csv(csv_content1)
#         payload1 = {"file_path": str(csv_file1), "requested_by": "test@example.com"}
#
#         result1 = await handle_bulk_import_question(payload1, worker_ctx)
#         assert result1["successful"] == 1
#
#         # Second import with updated data
#         csv_content2 = """question_id,text,difficulty,knowledge_node_id,options,correct_answer
# q_update,Updated question text,hard,test_node_2,"[""X"",""Y"",""Z""]",2
# """
#         csv_file2 = create_temp_csv(csv_content2)
#         payload2 = {"file_path": str(csv_file2), "requested_by": "test@example.com"}
#
#         result2 = await handle_bulk_import_question(payload2, worker_ctx)
#         assert result2["successful"] == 1
#
#         # Verify question was updated
#         async with worker_ctx.neo4j_scoped_connection():
#             q = await asyncio.to_thread(
#                 neo.MultipleChoice.nodes.get,
#                 question_id="q_update"
#             )
#             assert q.text == "Updated question text"
#             assert q.difficulty == "hard"
#             assert q.correct_answer == 2
#
#             # Verify relationship was updated
#             kn = await asyncio.to_thread(q.knowledge_node.single)
#             assert kn.node_id == "test_node_2"
#
#
# # =============================================================================
# # Test handle_bulk_import_relations
# # =============================================================================
#
#
# @pytest.mark.asyncio
# class TestBulkImportRelations:
#     """Test suite for bulk importing knowledge node relationships."""
#
#     @pytest_asyncio.fixture(scope="function")
#     async def multiple_nodes_in_neo4j(
#         self,
#         worker_ctx: WorkerContext,
#         test_course_in_neo4j: neo.Course,
#     ) -> AsyncGenerator[list[neo.KnowledgeNode], Any]:
#         """Create multiple test nodes for relationship tests."""
#         nodes = []
#         for i in range(1, 5):
#             node = neo.KnowledgeNode(
#                 node_id=f"rel_node_{i}",
#                 node_name=f"Relation Node {i}",
#                 description=f"Node {i} for testing relationships"
#             )
#             nodes.append(node)
#
#         async with worker_ctx.neo4j_scoped_connection():
#             for node in nodes:
#                 await asyncio.to_thread(node.save)
#                 await asyncio.to_thread(node.course.connect, test_course_in_neo4j)
#
#         yield nodes
#
#     async def test_import_relations_success(
#         self,
#         worker_ctx: WorkerContext,
#         multiple_nodes_in_neo4j: list[neo.KnowledgeNode],
#     ):
#         """Test successful bulk import of relationships."""
#         csv_content = """from_node_id,to_node_id,relationship_type
# rel_node_1,rel_node_2,HAS_PREREQUISITES
# rel_node_1,rel_node_3,HAS_SUBTOPIC
# rel_node_2,rel_node_4,IS_EXAMPLE_OF
# """
#         csv_file = create_temp_csv(csv_content)
#
#         payload = {
#             "file_path": str(csv_file),
#             "requested_by": "test@example.com"
#         }
#
#         result = await handle_bulk_import_relations(payload, worker_ctx)
#
#         assert result["status"] == "completed"
#         assert result["total_rows"] == 3
#         assert result["successful"] == 3
#         assert result["failed"] == 0
#
#         # Verify relationships were created
#         async with worker_ctx.neo4j_scoped_connection():
#             node1 = await asyncio.to_thread(
#                 neo.KnowledgeNode.nodes.get,
#                 node_id="rel_node_1"
#             )
#
#             # Check HAS_PREREQUISITES
#             prereq = await asyncio.to_thread(
#                 lambda: node1.prerequisites.is_connected(
#                     neo.KnowledgeNode.nodes.get(node_id="rel_node_2")
#                 )
#             )
#             assert prereq is True
#
#             # Check HAS_SUBTOPIC
#             subtopic = await asyncio.to_thread(
#                 lambda: node1.subtopic.is_connected(
#                     neo.KnowledgeNode.nodes.get(node_id="rel_node_3")
#                 )
#             )
#             assert subtopic is True
#
#     async def test_import_relations_invalid_type(
#         self,
#         worker_ctx: WorkerContext,
#         multiple_nodes_in_neo4j: list[neo.KnowledgeNode],
#     ):
#         """Test import fails gracefully with invalid relationship type."""
#         csv_content = """from_node_id,to_node_id,relationship_type
# rel_node_1,rel_node_2,HAS_PREREQUISITES
# rel_node_1,rel_node_3,INVALID_TYPE
# rel_node_2,rel_node_4,HAS_SUBTOPIC
# """
#         csv_file = create_temp_csv(csv_content)
#
#         payload = {
#             "file_path": str(csv_file),
#             "requested_by": "test@example.com"
#         }
#
#         result = await handle_bulk_import_relations(payload, worker_ctx)
#
#         assert result["status"] == "completed"
#         assert result["successful"] == 2
#         assert result["failed"] == 1
#         assert "INVALID_TYPE" in result["errors"][0]["error"]
#
#     async def test_import_relations_nonexistent_nodes(
#         self,
#         worker_ctx: WorkerContext,
#         multiple_nodes_in_neo4j: list[neo.KnowledgeNode],
#     ):
#         """Test import fails gracefully when nodes don't exist."""
#         csv_content = """from_node_id,to_node_id,relationship_type
# rel_node_1,rel_node_2,HAS_PREREQUISITES
# nonexistent,rel_node_3,HAS_SUBTOPIC
# rel_node_1,nonexistent,IS_EXAMPLE_OF
# """
#         csv_file = create_temp_csv(csv_content)
#
#         payload = {
#             "file_path": str(csv_file),
#             "requested_by": "test@example.com"
#         }
#
#         result = await handle_bulk_import_relations(payload, worker_ctx)
#
#         assert result["status"] == "completed"
#         assert result["successful"] == 1
#         assert result["failed"] == 2
#         assert len(result["errors"]) == 2
#
#     async def test_import_relations_idempotent(
#         self,
#         worker_ctx: WorkerContext,
#         multiple_nodes_in_neo4j: list[neo.KnowledgeNode],
#     ):
#         """Test that importing same relationship twice is idempotent."""
#         csv_content = """from_node_id,to_node_id,relationship_type
# rel_node_1,rel_node_2,HAS_PREREQUISITES
# """
#         # Import first time
#         csv_file1 = create_temp_csv(csv_content)
#         payload1 = {"file_path": str(csv_file1), "requested_by": "test@example.com"}
#         result1 = await handle_bulk_import_relations(payload1, worker_ctx)
#         assert result1["successful"] == 1
#
#         # Import second time (same relationship)
#         csv_file2 = create_temp_csv(csv_content)
#         payload2 = {"file_path": str(csv_file2), "requested_by": "test@example.com"}
#         result2 = await handle_bulk_import_relations(payload2, worker_ctx)
#         assert result2["successful"] == 1  # Should still succeed
#
#         # Verify only one relationship exists
#         async with worker_ctx.neo4j_scoped_connection():
#             node1 = await asyncio.to_thread(
#                 neo.KnowledgeNode.nodes.get,
#                 node_id="rel_node_1"
#             )
#             prereqs = await asyncio.to_thread(
#                 lambda: list(node1.prerequisites.all())
#             )
#             assert len(prereqs) == 1
#             assert prereqs[0].node_id == "rel_node_2"
#
#     async def test_import_relations_all_types(
#         self,
#         worker_ctx: WorkerContext,
#         multiple_nodes_in_neo4j: list[neo.KnowledgeNode],
#     ):
#         """Test importing all three relationship types."""
#         csv_content = """from_node_id,to_node_id,relationship_type
# rel_node_1,rel_node_2,HAS_PREREQUISITES
# rel_node_1,rel_node_3,HAS_SUBTOPIC
# rel_node_1,rel_node_4,IS_EXAMPLE_OF
# """
#         csv_file = create_temp_csv(csv_content)
#
#         payload = {
#             "file_path": str(csv_file),
#             "requested_by": "test@example.com"
#         }
#
#         result = await handle_bulk_import_relations(payload, worker_ctx)
#
#         assert result["status"] == "completed"
#         assert result["successful"] == 3
#
#         # Verify all three types
#         async with worker_ctx.neo4j_scoped_connection():
#             node1 = await asyncio.to_thread(
#                 neo.KnowledgeNode.nodes.get,
#                 node_id="rel_node_1"
#             )
#
#             prereqs = await asyncio.to_thread(lambda: list(node1.prerequisites.all()))
#             assert len(prereqs) == 1
#
#             subtopics = await asyncio.to_thread(lambda: list(node1.subtopic.all()))
#             assert len(subtopics) == 1
#
#             examples = await asyncio.to_thread(
#                 lambda: list(node1.concept_this_is_example_of.all())
#             )
#             assert len(examples) == 1
#
#
# # =============================================================================
# # Integration Tests
# # =============================================================================
#
#
# @pytest.mark.asyncio
# class TestBulkImportIntegration:
#     """Integration tests for the complete bulk import workflow."""
#
#     async def test_complete_import_workflow(
#         self,
#         worker_ctx: WorkerContext,
#         test_course_in_neo4j: neo.Course,
#     ):
#         """Test the complete workflow: nodes -> relations -> questions."""
#         # Step 1: Import nodes
#         nodes_csv = f"""node_id,name,description,course_id
# workflow_node_1,Basics,Basic concepts,{TEST_COURSE_ID}
# workflow_node_2,Advanced,Advanced concepts,{TEST_COURSE_ID}
# """
#         nodes_file = create_temp_csv(nodes_csv)
#         nodes_result = await handle_bulk_import_nodes(
#             {"file_path": str(nodes_file), "requested_by": "test@example.com"},
#             worker_ctx
#         )
#         assert nodes_result["successful"] == 2
#
#         # Step 2: Import relationships
#         relations_csv = """from_node_id,to_node_id,relationship_type
# workflow_node_2,workflow_node_1,HAS_PREREQUISITES
# """
#         relations_file = create_temp_csv(relations_csv)
#         relations_result = await handle_bulk_import_relations(
#             {"file_path": str(relations_file), "requested_by": "test@example.com"},
#             worker_ctx
#         )
#         assert relations_result["successful"] == 1
#
#         # Step 3: Import questions
#         questions_csv = """question_id,text,difficulty,knowledge_node_id,options,correct_answer
# workflow_q1,Basic question,easy,workflow_node_1,"[""A"",""B""]",0
# workflow_q2,Advanced question,hard,workflow_node_2,"[""X"",""Y"",""Z""]",2
# """
#         questions_file = create_temp_csv(questions_csv)
#         questions_result = await handle_bulk_import_question(
#             {"file_path": str(questions_file), "requested_by": "test@example.com"},
#             worker_ctx
#         )
#         assert questions_result["successful"] == 2
#
#         # Verify complete graph structure
#         async with worker_ctx.neo4j_scoped_connection():
#             # Check nodes exist
#             node1 = await asyncio.to_thread(
#                 neo.KnowledgeNode.nodes.get,
#                 node_id="workflow_node_1"
#             )
#             node2 = await asyncio.to_thread(
#                 neo.KnowledgeNode.nodes.get,
#                 node_id="workflow_node_2"
#             )
#
#             # Check relationship
#             has_prereq = await asyncio.to_thread(
#                 lambda: node2.prerequisites.is_connected(node1)
#             )
#             assert has_prereq is True
#
#             # Check questions
#             q1 = await asyncio.to_thread(
#                 neo.MultipleChoice.nodes.get,
#                 question_id="workflow_q1"
#             )
#             q1_node = await asyncio.to_thread(q1.knowledge_node.single)
#             assert q1_node.node_id == "workflow_node_1"
#
#             q2 = await asyncio.to_thread(
#                 neo.MultipleChoice.nodes.get,
#                 question_id="workflow_q2"
#             )
#             q2_node = await asyncio.to_thread(q2.knowledge_node.single)
#             assert q2_node.node_id == "workflow_node_2"
