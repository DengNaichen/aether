# 在一个新的文件 app_logic.py 中

import psycopg2
from useless.config import DB_SETTINGS

def get_student_progress(student_id):
    """查询并返回一个学生所有知识点的学习状态"""
    sql = """
        SELECT 
            kn.node_id,
            kn.topic_name,
            -- 如果没有进度记录，则 mastery_level 为 NULL，我们用 COALESCE 转换为 'unseen'
            COALESCE(snp.mastery_level::text, 'unseen') AS mastery_level
        FROM 
            KnowledgeNodes kn
        LEFT JOIN 
            StudentNodeProgress snp ON kn.node_id = snp.node_id AND snp.student_id = %s;
    """
    conn = psycopg2.connect(**DB_SETTINGS)
    with conn.cursor() as cur:
        cur.execute(sql, (student_id,))
        progress = cur.fetchall()
    conn.close()
    
    # 将结果转换为更友好的字典格式
    progress_map = [{'node_id': row[0], 'topic': row[1], 'status': row[2]} for row in progress]
    return progress_map



# 继续在 app_logic.py 中添加

def update_node_mastery(student_id, node_id, new_mastery_level, student_name=None, student_email=None):
    """创建或更新一个学生对某个节点的掌握程度. 如果学生不存在，则先创建"""
    conn = psycopg2.connect(**DB_SETTINGS)
    try:
        with conn.cursor() as cur:
            # 检查学生是否存在
            cur.execute("SELECT student_id FROM Students WHERE student_id = %s;", (student_id,))
            if cur.fetchone() is None:
                # 如果学生不存在，并且提供了姓名和邮箱，则创建新学生
                if student_name and student_email:
                    # 这里我们假设 add_student 函数已经被正确实现
                    new_student_id = add_student(student_name, student_email)
                    if new_student_id is None:
                        print("Failed to add new student.")
                        return
                    student_id = new_student_id
                else:
                    print("Student does not exist and name/email were not provided.")
                    return

            # 更新或插入学习进度
            sql = """
                INSERT INTO StudentNodeProgress (student_id, node_id, mastery_level, is_studied, last_reviewed_at)
                VALUES (%s, %s, %s, TRUE, NOW())
                ON CONFLICT (student_id, node_id)
                DO UPDATE SET
                    mastery_level = EXCLUDED.mastery_level,
                    is_studied = TRUE,
                    last_reviewed_at = NOW();
            """
            cur.execute(sql, (student_id, node_id, new_mastery_level))
            conn.commit()
            print(f"Updated progress for student {student_id} on node {node_id} to '{new_mastery_level}'.")
    finally:
        conn.close()
    sql = """
        INSERT INTO StudentNodeProgress (student_id, node_id, mastery_level, is_studied, last_reviewed_at)
        VALUES (%s, %s, %s, TRUE, NOW())
        ON CONFLICT (student_id, node_id) 
        DO UPDATE SET 
            mastery_level = EXCLUDED.mastery_level,
            is_studied = TRUE,
            last_reviewed_at = NOW();
    """

# 你还需要一个函数来创建学生
def add_student(name, email):
    """添加一个新学生到数据库"""
    sql = "INSERT INTO Students (student_name, student_email) VALUES (%s, %s) RETURNING student_id;"
    conn = psycopg2.connect(**DB_SETTINGS)
    student_id = None
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (name, email))
            student_id = cur.fetchone()[0]
            conn.commit()
            print(f"Student '{name}' added with ID: {student_id}.")
    except psycopg2.IntegrityError:
        conn.rollback()
        print(f"Student with email '{email}' already exists.")
    finally:
        conn.close()
    return student_id