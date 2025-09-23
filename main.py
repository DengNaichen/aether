# main.py

import psycopg2
from config import DB_SETTINGS

# --- 1. 定义我们要插入的知识图谱数据 ---
# 以 G11 化学第一章为例
KNOWLEDGE_NODES_DATA = [
    {'topic_name': 'Matter', 'description': 'Anything that has mass and takes up space.', 'subject': 'G11 Chemistry'},
    {'topic_name': 'Pure Substance', 'description': 'A substance with a fixed chemical composition.', 'subject': 'G11 Chemistry'},
    {'topic_name': 'Mixture', 'description': 'A combination of two or more substances that are not chemically united.', 'subject': 'G11 Chemistry'},
    {'topic_name': 'Element', 'description': 'The simplest form of a pure substance.', 'subject': 'G11 Chemistry'},
    {'topic_name': 'Compound', 'description': 'A pure substance formed from two or more elements chemically united in fixed proportions.', 'subject': 'G11 Chemistry'},
    {'topic_name': 'Ionic Bond', 'description': 'A chemical bond formed through an electrostatic attraction between two oppositely charged ions.', 'subject': 'G11 Chemistry'},
    {'topic_name': 'Covalent Bond', 'description': 'A chemical bond that involves the sharing of electron pairs between atoms.', 'subject': 'G11 Chemistry'},
]

# 知识点之间的关系
# 注意：我们这里使用 topic_name，后面代码会将其转换为 node_id
KNOWLEDGE_EDGES_DATA = [
    # source, target, relationship
    ('Pure Substance', 'Matter', 'is_a_type_of'),
    ('Mixture', 'Matter', 'is_a_type_of'),
    ('Element', 'Pure Substance', 'is_a_type_of'),
    ('Compound', 'Pure Substance', 'is_a_type_of'),
    ('Ionic Bond', 'Compound', 'is_related_to'),
    ('Covalent Bond', 'Compound', 'is_related_to'),
]

# --- 2. 数据库操作函数 ---

def create_tables(cursor):
    """从 .sql 文件读取并执行 SQL 来创建表"""
    print("Creating tables from db_schema.sql...")
    with open('db_schema.sql', 'r') as f:
        cursor.execute(f.read())
    print("Tables created successfully.")

def insert_nodes(cursor, nodes):
    """批量插入知识节点数据"""
    print(f"Inserting {len(nodes)} nodes...")
    sql = "INSERT INTO KnowledgeNodes (topic_name, description, subject) VALUES (%s, %s, %s)"
    
    # 将字典列表转换为元组列表
    data_to_insert = [(node['topic_name'], node['description'], node['subject']) for node in nodes]
    
    # executemany 是高效的批量插入方法
    cursor.executemany(sql, data_to_insert)
    print("Nodes inserted successfully.")

def insert_edges(cursor, edges):
    """批量插入知识关联数据"""
    print(f"Inserting {len(edges)} edges...")
    
    # 这是一个关键步骤：我们需要先查询出 topic_name 对应的 node_id
    # 创建一个从 topic_name 到 node_id 的映射字典，避免多次查询数据库
    cursor.execute("SELECT node_id, topic_name FROM KnowledgeNodes")
    topic_to_id = {name: id for id, name in cursor.fetchall()}

    sql = "INSERT INTO KnowledgeEdges (source_node_id, target_node_id, relationship) VALUES (%s, %s, %s)"
    
    data_to_insert = []
    for source, target, rel in edges:
        source_id = topic_to_id.get(source)
        target_id = topic_to_id.get(target)
        if source_id and target_id:
            data_to_insert.append((source_id, target_id, rel))
        else:
            print(f"Warning: Could not find ID for edge '{source}' -> '{target}'. Skipping.")

    cursor.executemany(sql, data_to_insert)
    print("Edges inserted successfully.")


# --- 3. 主函数 ---

def main():
    """主执行函数"""
    conn = None
    try:
        # 连接到 PostgreSQL 数据库
        print("Connecting to the database...")
        conn = psycopg2.connect(**DB_SETTINGS)
        
        # 创建一个 cursor 对象，用来执行SQL命令
        # with 语句可以确保资源被正确关闭
        with conn.cursor() as cur:
            # 步骤 1: 创建表
            create_tables(cur)
            
            # 步骤 2: 插入节点数据
            insert_nodes(cur, KNOWLEDGE_NODES_DATA)
            
            # 步骤 3: 插入关联数据
            insert_edges(cur, KNOWLEDGE_EDGES_DATA)
            
        # 提交事务，让更改生效
        conn.commit()
        print("\nDatabase setup complete and data inserted successfully!")

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        # 如果发生错误，回滚所有更改
        if conn:
            conn.rollback()
    finally:
        # 确保数据库连接最后被关闭
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == '__main__':
    main()