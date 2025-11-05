#!/usr/bin/env python3
"""
Setup Development Course Data

Loads a persistent development course with:
- PostgreSQL: Course metadata
- Neo4j: Knowledge graph (48 nodes + relationships)
- Neo4j: 195 multiple choice questions

Data source: CSV files in Resource/ directory
"""

import asyncio
import csv
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import db_manager
# Import all models to avoid SQLAlchemy mapping errors
from app.models import Base, User, Course, Enrollment
from app.models import quiz  # Import quiz module for QuizAttempt
import app.models.neo4j_model as neo
from neomodel import DoesNotExist

# Course configuration
COURSE_ID = "g10_phys"
COURSE_NAME = "Grade 11 Physics - Chapter 1: Kinematics"
COURSE_DESCRIPTION = "Introduction to kinematics: displacement, velocity, and acceleration"

# Data files
RESOURCE_DIR = project_root / "Resource"
NODE_CSV = RESOURCE_DIR / "node.csv"
SUBTOPIC_CSV = RESOURCE_DIR / "has_subtopic.csv"
PREREQ_CSV = RESOURCE_DIR / "has_prerequisites.csv"
QUESTION_CSV = RESOURCE_DIR / "mcq.csv"


class SetupError(Exception):
    """Setup error"""
    pass


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


async def check_files_exist():
    """Check if all required data files exist"""
    print_section("Checking data files")

    files = [NODE_CSV, SUBTOPIC_CSV, PREREQ_CSV, QUESTION_CSV]
    missing = []

    for file_path in files:
        if file_path.exists():
            print(f"✅ {file_path.name}")
        else:
            print(f"❌ {file_path.name} - file not found")
            missing.append(file_path)

    if missing:
        raise SetupError(f"Missing required files: {[str(f) for f in missing]}")

    print("\nAll file checks passed!")


async def create_course_in_postgres():
    """Create course in PostgreSQL"""
    print_section("Creating course in PostgreSQL")

    async with db_manager.get_sql_session() as session:
        # Check if course already exists
        existing_course = await session.get(Course, COURSE_ID)

        if existing_course:
            print(f"ℹ️  Course {COURSE_ID} already exists, skipping creation")
            print(f"   Name: {existing_course.name}")
            print(f"   Description: {existing_course.description}")
            return False

        # Create new course
        course = Course(
            id=COURSE_ID,
            name=COURSE_NAME,
            description=COURSE_DESCRIPTION
        )
        session.add(course)
        await session.commit()

        print(f"✅ Successfully created course:")
        print(f"   ID: {COURSE_ID}")
        print(f"   Name: {COURSE_NAME}")
        print(f"   Description: {COURSE_DESCRIPTION}")
        return True


async def create_course_in_neo4j():
    """Create course node in Neo4j"""
    print_section("Creating course in Neo4j")

    async with db_manager.neo4j_scoped_connection():
        def _create_course():
            # Check if course already exists
            existing_course = neo.Course.nodes.get_or_none(course_id=COURSE_ID)

            if existing_course:
                print(f"ℹ️  Course {COURSE_ID} already exists in Neo4j, skipping creation")
                return False

            # Create new course
            course = neo.Course(
                course_id=COURSE_ID,
                course_name=COURSE_NAME
            ).save()

            print(f"✅ Successfully created course in Neo4j:")
            print(f"   course_id: {COURSE_ID}")
            print(f"   course_name: {COURSE_NAME}")
            return True

        return await asyncio.to_thread(_create_course)


async def import_knowledge_nodes():
    """Import knowledge nodes"""
    print_section("Importing knowledge nodes")

    async with db_manager.neo4j_scoped_connection():
        def _import_nodes():
            # Get course
            try:
                course = neo.Course.nodes.get(course_id=COURSE_ID)
            except DoesNotExist:
                raise SetupError(f"Course {COURSE_ID} does not exist in Neo4j")

            successful = 0
            failed = 0
            errors = []

            with open(NODE_CSV, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                total = sum(1 for _ in open(NODE_CSV)) - 1  # Count rows minus header

                # Reset file pointer
                f.seek(0)
                reader = csv.DictReader(f)

                for idx, row in enumerate(reader, start=1):
                    try:
                        node_id = row['node_id:ID'].strip()
                        node_name = row['node_name'].strip()
                        description = row['description'].strip()

                        # Check if node already exists
                        existing_node = neo.KnowledgeNode.nodes.get_or_none(node_id=node_id)

                        if existing_node:
                            # Update existing node
                            existing_node.node_name = node_name
                            existing_node.description = description
                            existing_node.save()

                            # Update course relationship if needed
                            if not existing_node.course.is_connected(course):
                                existing_node.course.disconnect_all()
                                existing_node.course.connect(course)
                        else:
                            # Create new node
                            new_node = neo.KnowledgeNode(
                                node_id=node_id,
                                node_name=node_name,
                                description=description
                            ).save()
                            new_node.course.connect(course)

                        successful += 1
                        if idx % 10 == 0 or idx == total:
                            print(f"  Progress: {idx}/{total} ({successful} succeeded, {failed} failed)")

                    except Exception as e:
                        failed += 1
                        errors.append({"node_id": row.get('node_id:ID', 'unknown'), "error": str(e)})

            print(f"\n✅ Knowledge nodes import completed:")
            print(f"   Total: {successful + failed}")
            print(f"   Succeeded: {successful}")
            print(f"   Failed: {failed}")

            if errors:
                print(f"\n❌ Error details:")
                for err in errors[:5]:  # Show first 5 errors
                    print(f"   - {err['node_id']}: {err['error']}")

            return successful, failed

        return await asyncio.to_thread(_import_nodes)


async def import_relationships(csv_file: Path, rel_type: str, rel_name: str):
    """Import relationships (generic function)"""
    print_section(f"Importing {rel_name}")

    async with db_manager.neo4j_scoped_connection():
        def _import_relations():
            successful = 0
            failed = 0
            errors = []

            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                total = sum(1 for _ in open(csv_file)) - 1

                f.seek(0)
                reader = csv.DictReader(f)

                for idx, row in enumerate(reader, start=1):
                    try:
                        # Handle different CSV formats
                        if ':START_ID(KnowledgeNode)' in row:
                            # Neo4j import format
                            from_node_id = row[':START_ID(KnowledgeNode)'].strip()
                            to_node_id = row[':END_ID(KnowledgeNode)'].strip()
                            weight = row.get('weight')  # Optional
                        else:
                            # Standard format
                            from_node_id = row['from_node_id'].strip()
                            to_node_id = row['to_node_id'].strip()
                            weight = row.get('weight')

                        # Get nodes
                        try:
                            source_node = neo.KnowledgeNode.nodes.get(node_id=from_node_id)
                            target_node = neo.KnowledgeNode.nodes.get(node_id=to_node_id)
                        except DoesNotExist as e:
                            raise ValueError(f"Node does not exist: {e}")

                        # Create relationship based on type
                        if rel_type == "HAS_SUBTOPIC":
                            if not source_node.subtopic.is_connected(target_node):
                                # Convert weight to float if present
                                weight_value = float(weight) if weight else 1.0
                                source_node.subtopic.connect(target_node, {'weight': weight_value})
                        elif rel_type == "IS_PREREQUISITE_FOR":
                            if not source_node.prerequisites.is_connected(target_node):
                                # Convert weight to float if present (default 1.0)
                                weight_value = float(weight) if weight else 1.0
                                source_node.prerequisites.connect(target_node, {'weight': weight_value})

                        successful += 1
                        if idx % 10 == 0 or idx == total:
                            print(f"  Progress: {idx}/{total} ({successful} succeeded, {failed} failed)")

                    except Exception as e:
                        failed += 1
                        errors.append({
                            "from": from_node_id if 'from_node_id' in locals() else 'unknown',
                            "to": to_node_id if 'to_node_id' in locals() else 'unknown',
                            "error": str(e)
                        })

            print(f"\n✅ {rel_name} import completed:")
            print(f"   Total: {successful + failed}")
            print(f"   Succeeded: {successful}")
            print(f"   Failed: {failed}")

            if errors:
                print(f"\n❌ Error details:")
                for err in errors[:5]:
                    print(f"   - {err['from']} -> {err['to']}: {err['error']}")

            return successful, failed

        return await asyncio.to_thread(_import_relations)


async def import_questions():
    """Import multiple choice questions"""
    print_section("Importing multiple choice questions")

    async with db_manager.neo4j_scoped_connection():
        def _import_questions():
            successful = 0
            failed = 0
            skipped = 0
            errors = []

            with open(QUESTION_CSV, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                total = sum(1 for _ in open(QUESTION_CSV)) - 1

                f.seek(0)
                reader = csv.DictReader(f)

                for idx, row in enumerate(reader, start=1):
                    try:
                        question_id = row['question_id'].strip()
                        knowledge_node_id = row['knowledge_node_id'].strip()
                        text = row['text'].strip()
                        options_str = row['options'].strip()
                        correct_answer = int(row['correct_answer'])
                        difficulty = row['difficulty'].strip().lower()

                        # Skip SAMPLE questions (commented out for development)
                        # Uncomment the following lines to skip SAMPLE questions in production
                        # if text.startswith('SAMPLE'):
                        #     skipped += 1
                        #     continue

                        # Parse options
                        try:
                            options = json.loads(options_str)
                        except json.JSONDecodeError:
                            raise ValueError(f"Invalid JSON format: {options_str}")

                        # Get knowledge node
                        try:
                            knowledge_node = neo.KnowledgeNode.nodes.get(node_id=knowledge_node_id)
                        except DoesNotExist:
                            raise ValueError(f"Knowledge node {knowledge_node_id} does not exist")

                        # Check if question exists
                        existing_q = neo.MultipleChoice.nodes.get_or_none(question_id=question_id)

                        if existing_q:
                            # Update existing question
                            existing_q.text = text
                            existing_q.difficulty = difficulty
                            existing_q.options = options
                            existing_q.correct_answer = correct_answer
                            existing_q.save()

                            # Update relationship if needed
                            current_node = existing_q.knowledge_node.single()
                            if current_node.node_id != knowledge_node_id:
                                existing_q.knowledge_node.reconnect(current_node, knowledge_node)
                        else:
                            # Create new question
                            new_q = neo.MultipleChoice(
                                question_id=question_id,
                                text=text,
                                difficulty=difficulty,
                                options=options,
                                correct_answer=correct_answer
                            ).save()
                            new_q.knowledge_node.connect(knowledge_node)

                        successful += 1
                        if idx % 20 == 0 or idx == total:
                            print(f"  Progress: {idx}/{total} ({successful} succeeded, {skipped} skipped, {failed} failed)")

                    except Exception as e:
                        failed += 1
                        errors.append({
                            "question_id": row.get('question_id', 'unknown'),
                            "error": str(e)
                        })

            print(f"\n✅ Multiple choice questions import completed:")
            print(f"   Total: {successful + skipped + failed}")
            print(f"   Succeeded: {successful}")
            print(f"   Skipped (SAMPLE): {skipped}")
            print(f"   Failed: {failed}")

            if errors:
                print(f"\n❌ Error details:")
                for err in errors[:5]:
                    print(f"   - {err['question_id']}: {err['error']}")

            return successful, failed, skipped

        return await asyncio.to_thread(_import_questions)


async def verify_data():
    """Verify imported data"""
    print_section("Verifying data")

    async with db_manager.neo4j_scoped_connection():
        def _verify():
            # Count nodes
            course = neo.Course.nodes.get_or_none(course_id=COURSE_ID)
            if not course:
                print("❌ Course does not exist")
                return

            # Use Cypher to count related nodes
            from neomodel import db as neomodel_db

            # Count knowledge nodes
            result = neomodel_db.cypher_query(
                "MATCH (c:Course {course_id: $course_id})<-[:BELONGS_TO]-(n:KnowledgeNode) RETURN count(n)",
                {"course_id": COURSE_ID}
            )
            node_count = result[0][0][0] if result[0] else 0

            # Count questions
            result = neomodel_db.cypher_query(
                """
                MATCH (c:Course {course_id: $course_id})<-[:BELONGS_TO]-(n:KnowledgeNode)
                <-[:TESTS]-(q:MultipleChoice)
                RETURN count(q)
                """,
                {"course_id": COURSE_ID}
            )
            question_count = result[0][0][0] if result[0] else 0

            # Count relationships
            result = neomodel_db.cypher_query(
                """
                MATCH (c:Course {course_id: $course_id})<-[:BELONGS_TO]-(n:KnowledgeNode)
                -[r:HAS_SUBTOPIC]->()
                RETURN count(r)
                """,
                {"course_id": COURSE_ID}
            )
            subtopic_count = result[0][0][0] if result[0] else 0

            result = neomodel_db.cypher_query(
                """
                MATCH (c:Course {course_id: $course_id})<-[:BELONGS_TO]-(n:KnowledgeNode)
                -[r:IS_PREREQUISITE_FOR]->()
                RETURN count(r)
                """,
                {"course_id": COURSE_ID}
            )
            prereq_count = result[0][0][0] if result[0] else 0

            print(f"✅ Data verification:")
            print(f"   Course: {COURSE_ID}")
            print(f"   Knowledge nodes: {node_count}")
            print(f"   Questions: {question_count}")
            print(f"   Subtopic relationships (HAS_SUBTOPIC): {subtopic_count}")
            print(f"   Prerequisite relationships (IS_PREREQUISITE_FOR): {prereq_count}")

        await asyncio.to_thread(_verify)


async def main():
    """Main function"""
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║         Development Environment Data Loader                ║
║                                                            ║
║   Course: Grade 11 Physics - Chapter 1: Kinematics         ║
║   Course ID: g10_phys                                      ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
""")

    try:
        # Step 1: Check files
        await check_files_exist()

        # Step 2: Create course in PostgreSQL
        await create_course_in_postgres()

        # Step 3: Create course in Neo4j
        await create_course_in_neo4j()

        # Step 4: Import knowledge nodes
        await import_knowledge_nodes()

        # Step 5: Import subtopic relationships
        await import_relationships(
            SUBTOPIC_CSV,
            "HAS_SUBTOPIC",
            "subtopic relationships (HAS_SUBTOPIC)"
        )

        # Step 6: Import prerequisite relationships
        await import_relationships(
            PREREQ_CSV,
            "IS_PREREQUISITE_FOR",
            "prerequisite relationships (IS_PREREQUISITE_FOR)"
        )

        # Step 7: Import questions
        await import_questions()

        # Step 8: Verify data
        await verify_data()

        print_section("Completed")
        print("""
✅ Development course data loading completed!

Data persistence notes:
- PostgreSQL data is stored in Docker volume 'postgres_data'
- Neo4j data is stored in Docker volume 'neo4j_data'
- Data will persist unless you run 'docker-compose down -v'

Usage tips:
- Restart containers: docker-compose restart
- View logs: docker-compose logs -f web
- Neo4j browser: http://localhost:7474 (neo4j/neo4j_password)
- Clean data: python scripts/cleanup_dev_course.py

Start developing! 🚀
""")

    except Exception as e:
        print_section("Error")
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
