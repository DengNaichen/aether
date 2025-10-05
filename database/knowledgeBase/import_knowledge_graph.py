import json
from neo4j import GraphDatabase

URI = "bolt://127.0.0.1:7687"
AUTH = ("neo4j", "d1997225")  # 修改为你的密码
DATABASE = "chapter3"

KNOWLEDGE_FILES = [
    "./g11_chem/chapter2.json"
]

def load_and_merge_data(file_list):
    all_nodes = []
    all_relationships = []
    
    print(f"开始从 {len(file_list)} 个文件中加载数据...")
    
    for file_name in file_list:
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                data = json.load(f)
                nodes = data.get("concepts", [])
                relationships = data.get("relationships", [])
                
                all_nodes.extend(nodes)
                all_relationships.extend(relationships)
                print(f"  - 成功加载 {file_name} (发现 {len(nodes)} 个节点, {len(relationships)} 个关系)")
        except FileNotFoundError:
            print(f"  - 错误: 文件 {file_name} 未找到，已跳过。")
        except json.JSONDecodeError:
            print(f"  - 错误: 文件 {file_name} 格式不正确，无法解析，已跳过。")

    # 去重
    unique_nodes = list({node['id']: node for node in all_nodes}.values())
    if len(all_nodes) != len(unique_nodes):
        print(f"提示：发现并移除了 {len(all_nodes) - len(unique_nodes)} 个重复的节点ID。")

    print(f"数据加载和合并完成。总计：{len(unique_nodes)} 个独立节点, {len(all_relationships)} 个关系。")
    
    return {"nodes": unique_nodes, "relationships": all_relationships}


def create_graph_in_neo4j(driver, data):
    with driver.session(database=DATABASE) as session:
        print(f"正在清空数据库 '{DATABASE}'...")
        session.run("MATCH (n) DETACH DELETE n")
        
        print("正在创建节点...")
        for node in data["nodes"]:
            # 使用默认标签 "Concept"
            session.run(
                "CREATE (n:Concept {id: $id, name: $name, definition: $definition})",
                id=node["id"],
                name=node.get("name"),
                definition=node.get("definition")
            )

        print("正在创建关系...")
        for rel in data["relationships"]:
            source_exists = any(node['id'] == rel['source_id'] for node in data['nodes'])
            target_exists = any(node['id'] == rel['target_id'] for node in data['nodes'])
            
            if source_exists and target_exists:
                query = f"""
                MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
                CREATE (a)-[:{rel['type']}]->(b)
                """
                session.run(query, source_id=rel["source_id"], target_id=rel["target_id"])
            else:
                print(f"  - 警告: 跳过关系 {rel['source_id']}->{rel['target_id']}，因为节点未在数据中定义。")

    print("图谱创建成功！")


if __name__ == "__main__":
    merged_graph_data = load_and_merge_data(KNOWLEDGE_FILES)
    
    if merged_graph_data["nodes"]:
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            print(f"正在验证与数据库 '{DATABASE}' 的连接...")
            driver.verify_connectivity()
            print("连接成功！")
            
            create_graph_in_neo4j(driver, merged_graph_data)
    else:
        print("没有加载到任何数据，程序退出。")
