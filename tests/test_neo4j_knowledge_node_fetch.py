"""
测试 Neo4j 知识节点查询函数

这个测试文件专门测试 courses.py 中的两个函数:
1. fetch_neo4j_knowledge_node_num - 获取单个课程的知识节点数
2. fetch_neo4j_knowledge_node_num_bulk - 批量获取多个课程的知识节点数

注意：这些测试使用 test fixtures 创建的测试数据，而不是依赖真实的 g10_phys 和 g10_chem 课程
"""

import asyncio
import pytest
from fastapi import HTTPException

from app.routes.courses import (
    fetch_neo4j_knowledge_node_num,
    fetch_neo4j_knowledge_node_num_bulk
)
import app.models.neo4j_model as neo
from tests.conftest import COURSE_ID_ONE


class TestFetchNeo4jKnowledgeNodeNum:
    """测试单个课程知识节点数查询"""

    @pytest.mark.asyncio
    async def test_fetch_knowledge_node_num_with_nodes(
        self,
        test_db_manager,
        nodes_in_neo4j_db
    ):
        """
        测试获取有知识节点的课程的知识节点数
        nodes_in_neo4j_db fixture 会创建 2 个知识节点
        """
        course_id = COURSE_ID_ONE  # 使用 fixture 创建的课程

        async with test_db_manager.neo4j_scoped_connection():
            result = await asyncio.to_thread(
                fetch_neo4j_knowledge_node_num,
                course_id
            )

            assert isinstance(result, int)
            assert result == 2  # nodes_in_neo4j_db 创建了 2 个节点
            print(f"{course_id} 课程的知识节点数: {result}")

    @pytest.mark.asyncio
    async def test_fetch_knowledge_node_num_without_nodes(
        self,
        test_db_manager,
        course_in_neo4j_db
    ):
        """
        测试获取没有知识节点的课程的知识节点数
        """
        course_id = course_in_neo4j_db.course_id

        async with test_db_manager.neo4j_scoped_connection():
            result = await asyncio.to_thread(
                fetch_neo4j_knowledge_node_num,
                course_id
            )

            assert isinstance(result, int)
            assert result == 0  # 没有添加任何知识节点
            print(f"{course_id} 课程的知识节点数: {result}")

    @pytest.mark.asyncio
    async def test_fetch_knowledge_node_num_for_nonexistent_course(
        self, test_db_manager
    ):
        """
        测试查询不存在的课程应该抛出 HTTPException
        """
        course_id = "nonexistent_course"

        async with test_db_manager.neo4j_scoped_connection():
            with pytest.raises(HTTPException) as exc_info:
                await asyncio.to_thread(
                    fetch_neo4j_knowledge_node_num,
                    course_id
                )

            assert exc_info.value.status_code == 404
            assert "not found" in str(exc_info.value.detail).lower()


class TestFetchNeo4jKnowledgeNodeNumBulk:
    """测试批量课程知识节点数查询"""

    @pytest.mark.asyncio
    async def test_fetch_knowledge_node_num_bulk_with_nodes(
        self,
        test_db_manager,
        nodes_in_neo4j_db
    ):
        """
        测试批量获取课程的知识节点数
        """
        course_id = COURSE_ID_ONE
        course_ids = [course_id]

        async with test_db_manager.neo4j_scoped_connection():
            result = await asyncio.to_thread(
                fetch_neo4j_knowledge_node_num_bulk,
                course_ids
            )

            assert isinstance(result, dict)
            assert course_id in result
            assert isinstance(result[course_id], int)
            assert result[course_id] == 2  # nodes_in_neo4j_db 创建了 2 个节点
            print(f"批量查询结果: {result}")

    @pytest.mark.asyncio
    async def test_fetch_knowledge_node_num_bulk_without_nodes(
        self,
        test_db_manager,
        course_in_neo4j_db
    ):
        """
        测试批量查询没有知识节点的课程
        """
        course_id = course_in_neo4j_db.course_id
        course_ids = [course_id]

        async with test_db_manager.neo4j_scoped_connection():
            result = await asyncio.to_thread(
                fetch_neo4j_knowledge_node_num_bulk,
                course_ids
            )

            assert isinstance(result, dict)
            # 没有知识节点的课程可能不会出现在结果中，或者返回 0
            if course_id in result:
                assert result[course_id] == 0

    @pytest.mark.asyncio
    async def test_fetch_knowledge_node_num_bulk_nonexistent_course(
        self,
        test_db_manager,
        course_in_neo4j_db
    ):
        """
        测试批量查询包含不存在的课程
        返回的字典中不应该包含不存在的课程
        """
        course_id = course_in_neo4j_db.course_id
        course_ids = [course_id, "nonexistent_course"]

        async with test_db_manager.neo4j_scoped_connection():
            result = await asyncio.to_thread(
                fetch_neo4j_knowledge_node_num_bulk,
                course_ids
            )

            assert isinstance(result, dict)
            # 不存在的课程不应该在结果中
            assert "nonexistent_course" not in result

    @pytest.mark.asyncio
    async def test_fetch_knowledge_node_num_bulk_empty_list(
        self, test_db_manager
    ):
        """
        测试批量查询空列表
        """
        course_ids = []

        async with test_db_manager.neo4j_scoped_connection():
            result = await asyncio.to_thread(
                fetch_neo4j_knowledge_node_num_bulk,
                course_ids
            )

            assert isinstance(result, dict)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_compare_single_and_bulk_results(
        self,
        test_db_manager,
        nodes_in_neo4j_db
    ):
        """
        测试单个查询和批量查询的结果是否一致
        """
        course_id = COURSE_ID_ONE
        course_ids = [course_id]

        async with test_db_manager.neo4j_scoped_connection():
            # 批量查询
            bulk_result = await asyncio.to_thread(
                fetch_neo4j_knowledge_node_num_bulk,
                course_ids
            )

            # 单个查询
            single_result = await asyncio.to_thread(
                fetch_neo4j_knowledge_node_num,
                course_id
            )

            # 比较结果
            assert bulk_result[course_id] == single_result, \
                f"课程 {course_id} 的单个查询和批量查询结果不一致"

            print(f"批量查询结果: {bulk_result}")
            print(f"单个查询结果: {single_result}")
            print("✓ 单个查询和批量查询结果一致")


class TestKnowledgeNodeRelationships:
    """测试知识节点与课程的关系"""

    @pytest.mark.asyncio
    async def test_knowledge_nodes_belong_to_course(
        self,
        test_db_manager,
        nodes_in_neo4j_db
    ):
        """
        验证知识节点正确地属于课程
        """
        course_id = COURSE_ID_ONE
        target_node, source_node = nodes_in_neo4j_db

        async with test_db_manager.neo4j_scoped_connection():
            # 通过 Cypher 查询获取知识节点
            from neomodel import db
            query = """
            MATCH (c:Course {course_id: $course_id})<-[:BELONGS_TO]-(k:KnowledgeNode)
            RETURN k.node_id AS node_id, k.node_name AS node_name
            """
            results, _ = await asyncio.to_thread(
                db.cypher_query,
                query,
                {"course_id": course_id}
            )

            print(f"\n课程 {course_id} 的知识节点:")
            for row in results:
                print(f"  - {row[1]} ({row[0]})")

            assert len(results) == 2, "应该有 2 个知识节点"

            # 验证反向查询也能找到课程
            first_node_id = results[0][0]
            node = await asyncio.to_thread(
                neo.KnowledgeNode.nodes.get_or_none,
                node_id=first_node_id
            )
            assert node is not None

            # 检查节点的课程关系
            related_course = await asyncio.to_thread(
                node.course.get_or_none
            )
            assert related_course is not None
            assert related_course.course_id == course_id
            print(f"✓ 知识节点 {first_node_id} 正确关联到课程 {course_id}")
