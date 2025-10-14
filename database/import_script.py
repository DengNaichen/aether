import json
from datetime import datetime, timezone

from neo4j import GraphDatabase

# --- 1. 配置您的数据库连接 ---
NEO4J_URI = "neo4j://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "d1997225"  # 已更新为您的密码
NEO4J_DATABASE = "g11physics"  # 已指定您的数据库名


JSON_FILE_PATH = "force_prob.json"

import json
from datetime import datetime, timezone

from neo4j import GraphDatabase

# --- 1. 您的配置信息 ---
NEO4J_URI = "neo4j://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "d1997225"
NEO4J_DATABASE = "g11physictest"

# --- 2. 您的JSON文件路径 ---
JSON_FILE_PATH = "force_prob.json"  # 已更新为您提到的文件名


class Neo4jImporter:
    def __init__(self, uri, user, password, db_name):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = db_name

    def close(self):
        self.driver.close()

    def import_problem(self, problem_data):
        with self.driver.session(database=self.database) as session:

            # --- 新增的关键代码：转换复杂字段为JSON字符串 ---
            # 检查'options'字段，如果它是列表，则转换为JSON字符串
            if "options" in problem_data and isinstance(problem_data["options"], list):
                problem_data["options"] = json.dumps(problem_data["options"])

            # 检查'answer'字段，如果它是字典，则转换为JSON字符串
            if "answer" in problem_data and isinstance(problem_data["answer"], dict):
                problem_data["answer"] = json.dumps(problem_data["answer"])
            # ----------------------------------------------------

            # 自动生成createdAt时间戳
            problem_data["createdAt"] = datetime.now(timezone.utc).isoformat()

            # Cypher查询语句保持不变
            query = (
                "MERGE (p:Problem {problemId: $props.problemId}) "
                "SET p += $props "
                "RETURN p.problemId AS id, p.content AS content"
            )

            result = session.run(query, props=problem_data)
            record = result.single()
            if record:
                print(f"成功向数据库 '{self.database}' 导入或更新习题: {record['id']}")
            else:
                print(f"导入习题 {problem_data['problemId']} 时出现问题。")


def main():
    importer = Neo4jImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE)
    try:
        with open(JSON_FILE_PATH, "r", encoding="utf-8") as f:
            problems = json.load(f)

        print(
            f"从 {JSON_FILE_PATH} 文件中找到 {len(problems)} 道习题，准备导入到数据库 '{NEO4J_DATABASE}'..."
        )
        for problem in problems:
            importer.import_problem(problem)
        print("\n所有习题导入完成！")
    except FileNotFoundError:
        print(f"错误：找不到JSON文件 {JSON_FILE_PATH}。请检查文件名和路径。")
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        importer.close()


if __name__ == "__main__":
    main()
