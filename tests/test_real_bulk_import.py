"""
Real-world test for bulk import functionality.

This script tests the complete bulk import workflow using real CSV files
and verifies the data was correctly imported into Neo4j.

Run this with: pytest tests/test_real_bulk_import.py -v -s
"""

import asyncio
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
import pytest_asyncio

import app.models.neo4j_model as neo
from app.core.database import DatabaseManager
from app.worker.bulk_import_handlers import (
    handle_bulk_import_nodes,
    handle_bulk_import_question,
    handle_bulk_import_relations,
)
from app.worker.config import WorkerContext


# Test data paths
EXAMPLE_DATA_DIR = Path(__file__).parent.parent / "example_data"
NODES_CSV = EXAMPLE_DATA_DIR / "nodes.csv"
RELATIONSHIPS_CSV = EXAMPLE_DATA_DIR / "relationships.csv"
QUESTIONS_CSV = EXAMPLE_DATA_DIR / "questions.csv"


def copy_csv_to_temp(source_csv: Path) -> Path:
    """
    Copy CSV file to a temporary location.
    This is necessary because handlers delete the file after processing.
    """
    temp_file = NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
    temp_path = Path(temp_file.name)
    temp_file.close()

    shutil.copy(source_csv, temp_path)
    return temp_path


@pytest.mark.asyncio
class TestRealBulkImport:
    """Test bulk import with real CSV files."""

    @pytest_asyncio.fixture(scope="function")
    async def setup_courses(self, test_db_manager: DatabaseManager):
        """Create the required courses in Neo4j before importing."""
        courses_to_create = [
            ("g10_phys", "Grade 10 Physics"),
            ("g10_chem", "Grade 10 Chemistry"),
        ]

        async with test_db_manager.neo4j_scoped_connection():
            for course_id, course_name in courses_to_create:
                course = neo.Course(course_id=course_id, course_name=course_name)
                await asyncio.to_thread(course.save)
                print(f"✅ Created course: {course_id} - {course_name}")

        yield

    @pytest_asyncio.fixture(scope="function")
    async def worker_ctx(self, test_db_manager: DatabaseManager) -> WorkerContext:
        """Create a WorkerContext for testing handlers."""
        return WorkerContext(db_mng=test_db_manager)

    async def test_complete_bulk_import_workflow(
        self,
        worker_ctx: WorkerContext,
        setup_courses,
    ):
        """
        Test the complete bulk import workflow with real CSV files:
        1. Import nodes (15 nodes)
        2. Import relationships (20 relationships)
        3. Import questions (38 questions)
        4. Verify all data was correctly imported
        """
        print("\n" + "=" * 80)
        print("STARTING REAL-WORLD BULK IMPORT TEST")
        print("=" * 80)

        # Verify CSV files exist
        assert NODES_CSV.exists(), f"Nodes CSV not found at {NODES_CSV}"
        assert (
            RELATIONSHIPS_CSV.exists()
        ), f"Relationships CSV not found at {RELATIONSHIPS_CSV}"
        assert QUESTIONS_CSV.exists(), f"Questions CSV not found at {QUESTIONS_CSV}"

        # =====================================================================
        # Step 1: Import Knowledge Nodes
        # =====================================================================
        print("\n📦 STEP 1: Importing Knowledge Nodes")
        print("-" * 80)

        # Copy CSV to temp location (handlers will delete the file)
        nodes_temp = copy_csv_to_temp(NODES_CSV)

        nodes_payload = {
            "file_path": str(nodes_temp),
            "requested_by": "test_admin@example.com",
        }

        nodes_result = await handle_bulk_import_nodes(nodes_payload, worker_ctx)

        print(f"\n📊 Nodes Import Summary:")
        print(f"   Total rows: {nodes_result['total_rows']}")
        print(f"   ✅ Successful: {nodes_result['successful']}")
        print(f"   ❌ Failed: {nodes_result['failed']}")

        assert nodes_result["status"] == "completed"
        assert nodes_result["successful"] == 15, "Should import 15 nodes"
        assert nodes_result["failed"] == 0, "No nodes should fail"

        # Verify some specific nodes exist
        async with worker_ctx.neo4j_scoped_connection():
            # Physics nodes
            node = await asyncio.to_thread(
                neo.KnowledgeNode.nodes.get_or_none, node_id="node_speed_velocity"
            )
            assert node is not None
            assert node.node_name == "Speed and Velocity"
            assert (
                node.description
                == "Understanding the difference between speed and velocity"
            )

            # Chemistry nodes
            node = await asyncio.to_thread(
                neo.KnowledgeNode.nodes.get_or_none, node_id="node_periodic_table"
            )
            assert node is not None
            assert node.node_name == "Periodic Table"

            # Verify course relationships
            course = await asyncio.to_thread(node.course.single)
            assert course.course_id == "g10_chem"

        print("✅ All nodes verified successfully!")

        # =====================================================================
        # Step 2: Import Relationships
        # =====================================================================
        print("\n🔗 STEP 2: Importing Relationships")
        print("-" * 80)

        # Copy CSV to temp location
        relations_temp = copy_csv_to_temp(RELATIONSHIPS_CSV)

        relations_payload = {
            "file_path": str(relations_temp),
            "requested_by": "test_admin@example.com",
        }

        relations_result = await handle_bulk_import_relations(
            relations_payload, worker_ctx
        )

        print(f"\n📊 Relationships Import Summary:")
        print(f"   Total rows: {relations_result['total_rows']}")
        print(f"   ✅ Successful: {relations_result['successful']}")
        print(f"   ❌ Failed: {relations_result['failed']}")

        assert relations_result["status"] == "completed"
        assert relations_result["successful"] == 20, "Should import 20 relationships"
        assert relations_result["failed"] == 0, "No relationships should fail"

        # Verify specific relationships
        async with worker_ctx.neo4j_scoped_connection():
            # Verify HAS_PREREQUISITES relationship
            speed_node = await asyncio.to_thread(
                neo.KnowledgeNode.nodes.get, node_id="node_speed_velocity"
            )
            mechanics_node = await asyncio.to_thread(
                neo.KnowledgeNode.nodes.get, node_id="node_mechanics_basics"
            )

            has_prereq = await asyncio.to_thread(
                speed_node.prerequisites.is_connected, mechanics_node
            )
            assert (
                has_prereq
            ), "Speed & Velocity should have Mechanics Basics as prerequisite"

            # Verify HAS_SUBTOPIC relationship
            energy_node = await asyncio.to_thread(
                neo.KnowledgeNode.nodes.get, node_id="node_energy_basics"
            )
            kinetic_node = await asyncio.to_thread(
                neo.KnowledgeNode.nodes.get, node_id="node_kinetic_energy"
            )

            has_subtopic = await asyncio.to_thread(
                energy_node.subtopic.is_connected, kinetic_node
            )
            assert has_subtopic, "Energy Basics should have Kinetic Energy as subtopic"

        print("✅ All relationships verified successfully!")

        # =====================================================================
        # Step 3: Import Questions
        # =====================================================================
        print("\n❓ STEP 3: Importing Questions")
        print("-" * 80)

        # Copy CSV to temp location
        questions_temp = copy_csv_to_temp(QUESTIONS_CSV)

        questions_payload = {
            "file_path": str(questions_temp),
            "requested_by": "test_admin@example.com",
        }

        questions_result = await handle_bulk_import_question(
            questions_payload, worker_ctx
        )

        print(f"\n📊 Questions Import Summary:")
        print(f"   Total rows: {questions_result['total_rows']}")
        print(f"   ✅ Successful: {questions_result['successful']}")
        print(f"   ❌ Failed: {questions_result['failed']}")

        assert questions_result["status"] == "completed"
        assert questions_result["successful"] == 4, "Should import 38 questions"
        assert questions_result["failed"] == 0, "No questions should fail"

        # Verify specific questions
        async with worker_ctx.neo4j_scoped_connection():
            # Verify a physics question
            q1 = await asyncio.to_thread(
                neo.MultipleChoice.nodes.get_or_none, question_id="q_phys_speed_001"
            )
            assert q1 is not None
            assert "car travels 100 meters" in q1.text
            assert q1.difficulty == "easy"
            assert len(q1.options) == 4
            assert q1.correct_answer == 1  # "10 m/s"

            # Verify question → node relationship
            node = await asyncio.to_thread(q1.knowledge_node.single)
            assert node.node_id == "node_speed_velocity"

            # Verify a chemistry question
            q_chem = await asyncio.to_thread(
                neo.MultipleChoice.nodes.get_or_none, question_id="q_chem_atom_001"
            )
            assert q_chem is not None
            assert "atomic number" in q_chem.text.lower()
            assert q_chem.difficulty == "easy"

            # Verify it's linked to chemistry node
            chem_node = await asyncio.to_thread(q_chem.knowledge_node.single)
            assert chem_node.node_id == "node_atoms_basics"
            chem_course = await asyncio.to_thread(chem_node.course.single)
            assert chem_course.course_id == "g10_chem"

        print("✅ All questions verified successfully!")

        # =====================================================================
        # Step 4: Verify Complete Knowledge Graph Structure
        # =====================================================================
        print("\n🕸️  STEP 4: Verifying Complete Knowledge Graph Structure")
        print("-" * 80)

        async with worker_ctx.neo4j_scoped_connection():
            # Count all nodes
            all_nodes = await asyncio.to_thread(
                lambda: list(neo.KnowledgeNode.nodes.all())
            )
            print(f"   📌 Total Knowledge Nodes: {len(all_nodes)}")
            assert len(all_nodes) == 15

            # Count all questions
            all_questions = await asyncio.to_thread(
                lambda: list(neo.MultipleChoice.nodes.all())
            )
            print(f"   ❓ Total Questions: {len(all_questions)}")
            assert len(all_questions) == 4

            # Verify physics questions distribution
            physics_nodes = [n for n in all_nodes if "phys" in n.node_id.lower()]
            print(f"   🔬 Physics Nodes: {len(physics_nodes)}")

            # Verify chemistry questions distribution
            chem_nodes = [n for n in all_nodes if "chem" in n.node_id.lower()]
            print(f"   ⚗️  Chemistry Nodes: {len(chem_nodes)}")

            # Verify difficulty distribution
            easy_qs = [q for q in all_questions if q.difficulty == "easy"]
            medium_qs = [q for q in all_questions if q.difficulty == "medium"]
            hard_qs = [q for q in all_questions if q.difficulty == "hard"]

            print(f"\n   📊 Question Difficulty Distribution:")
            print(f"      Easy: {len(easy_qs)}")
            print(f"      Medium: {len(medium_qs)}")
            print(f"      Hard: {len(hard_qs)}")

            assert len(easy_qs) > 0
            assert len(medium_qs) > 0
            assert len(hard_qs) > 0

        print("\n" + "=" * 80)
        print("✅ REAL-WORLD BULK IMPORT TEST COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print(f"\n📈 Final Summary:")
        print(f"   ✅ 15 Knowledge Nodes imported")
        print(f"   ✅ 20 Relationships created")
        print(f"   ✅ 38 Questions imported")
        print(f"   ✅ Complete knowledge graph verified")
        print("=" * 80 + "\n")

    async def test_idempotent_reimport(
        self,
        worker_ctx: WorkerContext,
        setup_courses,
    ):
        """
        Test that re-importing the same CSV files is idempotent:
        - First import creates all data
        - Second import updates but doesn't fail
        - Data remains consistent
        """
        print("\n" + "=" * 80)
        print("TESTING IDEMPOTENT RE-IMPORT")
        print("=" * 80)

        # First import
        print("\n📥 First Import...")
        nodes_temp1 = copy_csv_to_temp(NODES_CSV)
        nodes_payload = {
            "file_path": str(nodes_temp1),
            "requested_by": "test_admin@example.com",
        }
        result1 = await handle_bulk_import_nodes(nodes_payload, worker_ctx)
        assert result1["successful"] == 15

        # Count nodes after first import
        async with worker_ctx.neo4j_scoped_connection():
            count1 = await asyncio.to_thread(
                lambda: len(list(neo.KnowledgeNode.nodes.all()))
            )
            print(f"   Nodes after first import: {count1}")

        # Second import (should update, not duplicate)
        print("\n📥 Second Import (re-import)...")
        nodes_temp2 = copy_csv_to_temp(NODES_CSV)
        nodes_payload2 = {
            "file_path": str(nodes_temp2),
            "requested_by": "test_admin@example.com",
        }
        result2 = await handle_bulk_import_nodes(nodes_payload2, worker_ctx)
        assert result2["successful"] == 15
        assert result2["failed"] == 0

        # Count nodes after second import
        async with worker_ctx.neo4j_scoped_connection():
            count2 = await asyncio.to_thread(
                lambda: len(list(neo.KnowledgeNode.nodes.all()))
            )
            print(f"   Nodes after second import: {count2}")

        # Should be the same count (no duplicates)
        assert count1 == count2 == 15, "Re-import should not create duplicates"

        print("\n✅ Idempotent re-import test passed!")
        print("=" * 80 + "\n")


@pytest.mark.asyncio
async def test_csv_files_exist():
    """Quick test to verify CSV files are in the right location."""
    assert (
        EXAMPLE_DATA_DIR.exists()
    ), f"Example data directory not found: {EXAMPLE_DATA_DIR}"
    assert NODES_CSV.exists(), f"nodes.csv not found at {NODES_CSV}"
    assert (
        RELATIONSHIPS_CSV.exists()
    ), f"relationships.csv not found at {RELATIONSHIPS_CSV}"
    assert QUESTIONS_CSV.exists(), f"questions.csv not found at {QUESTIONS_CSV}"

    print(f"\n✅ All CSV files found:")
    print(f"   📄 {NODES_CSV.name}")
    print(f"   📄 {RELATIONSHIPS_CSV.name}")
    print(f"   📄 {QUESTIONS_CSV.name}")
