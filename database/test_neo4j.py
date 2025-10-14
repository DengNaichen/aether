import json

from neo4j import GraphDatabase

# --- 数据库连接信息 ---
# 请确保URI、用户名、密码和数据库名与您的Neo4j设置匹配
URI = "neo4j://localhost:7687"
AUTH = ("neo4j", "d1997225")  # 在这里替换成你的密码
DATABASE = "g11physics"  # 确保这里的数据库名和你的设置一致

# --- 新增：定义要加载的JSON文件列表 ---
# 你可以在这里添加更多的文件名，脚本会自动处理
KNOWLEDGE_FILES = [
    "vector.json",
    "reference_frame.json",
    "position.json",
    "displacement.json",
]


def load_and_merge_data(file_list):
    """
    读取所有指定的JSON文件，并将它们的节点和关系合并。
    """
    all_nodes = []
    all_relationships = []

    print(f"开始从 {len(file_list)} 个文件中加载数据...")

    for file_name in file_list:
        try:
            with open(file_name, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 使用 .get() 方法安全地获取节点和关系，如果某个文件没有nodes或relationships键，也不会报错
                nodes = data.get("nodes", [])
                relationships = data.get("relationships", [])

                all_nodes.extend(nodes)
                all_relationships.extend(relationships)
                print(
                    f"  - 成功加载 {file_name} (发现 {len(nodes)} 个节点, {len(relationships)} 个关系)"
                )
        except FileNotFoundError:
            print(f"  - 错误: 文件 {file_name} 未找到，已跳过。")
        except json.JSONDecodeError:
            print(f"  - 错误: 文件 {file_name} 格式不正确，无法解析，已跳过。")

    # 使用字典来去重节点，防止不同文件中有重复的节点ID
    unique_nodes = list({node["id"]: node for node in all_nodes}.values())

    if len(all_nodes) != len(unique_nodes):
        print(
            f"提示：发现并移除了 {len(all_nodes) - len(unique_nodes)} 个重复的节点ID。"
        )

    print(
        f"数据加载和合并完成。总计：{len(unique_nodes)} 个独立节点, {len(all_relationships)} 个关系。"
    )

    return {"nodes": unique_nodes, "relationships": all_relationships}


def create_graph_in_neo4j(driver, data):
    """连接到Neo4j并创建图谱 (此函数与之前版本相同)"""
    with driver.session(database=DATABASE) as session:
        print(f"正在清空数据库 '{DATABASE}'...")
        session.run("MATCH (n) DETACH DELETE n")

        print("正在创建节点...")
        for node in data["nodes"]:
            labels = ":".join(node["labels"])
            session.run(
                f"CREATE (n:{labels} {{id: $id, name: $name}})",
                id=node["id"],
                name=node["name"],
            )

        print("正在创建关系...")
        for rel in data["relationships"]:
            # 检查关系中的源和目标节点是否存在于节点列表中
            source_exists = any(node["id"] == rel["source"] for node in data["nodes"])
            target_exists = any(node["id"] == rel["target"] for node in data["nodes"])

            if source_exists and target_exists:
                query = f"MATCH (a {{id: $source_id}}) MATCH (b {{id: $target_id}}) CREATE (a)-[:{rel['type']}]->(b)"
                session.run(query, source_id=rel["source"], target_id=rel["target"])
            else:
                print(
                    f"  - 警告: 跳过关系 {rel['source']}->{rel['target']}，因为节点未在数据中定义。"
                )

    print("图谱创建成功！")


if __name__ == "__main__":
    # 1. 从多个JSON文件加载并合并数据
    merged_graph_data = load_and_merge_data(KNOWLEDGE_FILES)

    # 2. 如果数据不为空，则连接数据库并创建图谱
    if merged_graph_data["nodes"]:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            # --- 这是需要修改的行 ---
            # 告诉驱动程序去验证你指定的数据库，而不是默认的 "neo4j"
            print(f"正在验证与数据库 '{DATABASE}' 的连接...")
            driver.verify_connectivity(database=DATABASE)
            print("连接成功！")

            # 后续代码无需改动
            create_graph_in_neo4j(driver, merged_graph_data)
    else:
        print("没有加载到任何数据，程序退出。")
