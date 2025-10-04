import psycopg2
from app.config import DB_SETTINGS


def create_student_tables(cursor):
    """从 .sql 文件读取并执行 SQL 来创建表"""
    print("Creating tables from db_schema.sql...")
    with open('student.sql', 'r') as f:
        cursor.execute(f.read())
    print("Tables created successfully.")



def main_student_tables():
    conn = None
    try:
        print("Connecting to the database...")
        conn = psycopg2.connect(**DB_SETTINGS)

        with conn.cursor() as cur:
            create_student_tables(cur)
        conn.commit()
        print("\nDatabase setup complete and data inserted successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")


if __name__ == "__main__":
    main_student_tables()