# this file contain two parts
# 1. create a table in the sql database, no api offered
# 2. when create the course table in sql, a neo4j database also created
#    with the same course name.
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models import Course

async def create_course_table_in_sql(
        course_name,
        description,
        db: AsyncSession = Depends() # TODO: 我这里要使用UUID吗?
):
    pass

async def create_neo4j_database(
        course_name: str,
        course_id: UUID,
        description: str,
        session: AsyncSession = Depends()
):
    """
    TODO: each neo4j database is a course????
    TODO: 虽然这么做降低了知识图的复杂度, 但是并没有给以后的设计留出可以拓展的空间
    TODO: 是不是应该把每一个学科设计成一个database? 但是如何保证11年级的学生不会接触到12年级的课程?
        或者12年级的学生不会在复习11年级的时被困住呢? 比如一个12年级才开始使用的学生?
    """
    pass

async def create_empty_course(course_id, course_name):
# TODO: here we need to combile both function together
    pass


# after we have an empty course: we need to initilized it
async def initialize_neo4j_database(
        course_name: str,
        course_id: UUID,
):
    await import_knowledge_nodes()
    await import_problem_nodes()
    await update_knowledge_graph()
    await update_problems()



#