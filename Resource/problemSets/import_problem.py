import json
import logging
import uuid
from datetime import datetime

from neo4j import GraphDatabase, exceptions


# --- 1. Configuration ---
class Config:
    """Configuration settings for the import script."""

    URI = "bolt://localhost:7687"
    AUTH = ("neo4j", "d1997225")
    DATABASE = "chapter3"
    # Use glob to find all relevant JSON files
    PROBLEMS_FILES_PATTERN = "./g11_chem/*.json"
    ID_PREFIX = "test"


# --- 2. Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# --- 3. Data Importer Class ---
class ProblemImporter:
    """Imports problems and their relationships into Neo4j."""

    def __init__(self, uri, auth, database):
        self.driver = GraphDatabase.driver(uri, auth=auth)
        self.database = database

    def close(self):
        self.driver.close()

    def load_and_merge_data(self, file_pattern):
        """Loads problem data from multiple JSON files."""
        all_problems = []

        import glob

        file_list = glob.glob(file_pattern)

        logging.info(f"Loading data from {len(file_list)} files...")
        for file_name in file_list:
            try:
                with open(file_name, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    problems = data.get("problems", [])
                    all_problems.extend(problems)
                    logging.info(
                        f"  - Successfully loaded {file_name} ({len(problems)} problems found)"
                    )
            except FileNotFoundError:
                logging.error(f"  - Error: File not found {file_name}")
            except json.JSONDecodeError:
                logging.error(f"  - Error: Invalid JSON format in {file_name}")
        return all_problems

    def create_problem_id_and_data(self, problems, id_prefix):
        """Generates a unique ID and timestamp for each problem."""
        for problem in problems:
            problem["problemId"] = f"{id_prefix}_{uuid.uuid4().hex[:8].upper()}"
            problem["createdAt"] = datetime.now().isoformat()
        return problems

    def create_graph_in_neo4j(self, problems):
        """Imports problems and their relationships into Neo4j."""
        problems_data = [
            {
                "id": p["problemId"],
                "question": p.get("question"),
                "options": p.get("options"),
                "correct": p.get("correct"),
                "difficulty": p.get("difficulty"),
                "knowledge_label": p.get("knowledge_label"),
            }
            for p in problems
        ]

        query = """
        UNWIND $problems AS problem_data
        MERGE (p:Problem {id: problem_data.id})
        ON CREATE SET
            p.question = problem_data.question,
            p.options = problem_data.options,
            p.difficulty = problem_data.difficulty,
            p.correct = problem_data.correct
        WITH p, problem_data
        MATCH (k:Concept {id: problem_data.knowledge_label})
        MERGE (p)-[:TESTED]->(k)
        """

        try:
            with self.driver.session(database=self.database) as session:
                logging.info(
                    "Importing problems and their relationships to concepts..."
                )
                result = session.run(query, problems=problems_data)
                summary = result.consume()

                nodes_created = summary.counters.nodes_created
                relationships_created = summary.counters.relationships_created

                logging.info(
                    f"Successfully created {nodes_created} nodes and {relationships_created} relationships."
                )
                logging.info(f"Finished importing {len(problems_data)} problems.")

        except exceptions.ServiceUnavailable as e:
            logging.error(f"Neo4j connection failed: {e}")
        except Exception as e:
            logging.error(f"An error occurred during the Neo4j import: {e}")


# --- 4. Main Execution ---
if __name__ == "__main__":
    importer = ProblemImporter(Config.URI, Config.AUTH, Config.DATABASE)

    try:
        logging.info(f"Verifying connection to database '{Config.DATABASE}'...")
        importer.driver.verify_connectivity()
        logging.info("Connection successful!")

        merged_data = importer.load_and_merge_data(Config.PROBLEMS_FILES_PATTERN)
        if merged_data:
            problems_with_ids = importer.create_problem_id_and_data(
                merged_data, Config.ID_PREFIX
            )
            importer.create_graph_in_neo4j(problems_with_ids)
        else:
            logging.warning("No problems found to import.")

    finally:
        importer.close()
        logging.info("Script finished.")
