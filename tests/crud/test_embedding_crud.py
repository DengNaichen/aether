import pytest

from app.core.config import settings
from app.crud.knowledge_node import (
    get_node_by_id,
    get_nodes_missing_embeddings,
    update_node_embeddings,
)
from app.models.knowledge_graph import KnowledgeGraph
from app.models.knowledge_node import KnowledgeNode


def _vec(val: float = 0.1) -> list[float]:
    return [val] * settings.GEMINI_EMBEDDING_DIM


@pytest.mark.asyncio
async def test_get_nodes_missing_embeddings_returns_missing_and_outdated(
    test_db, user_in_db
):
    graph = KnowledgeGraph(
        owner_id=user_in_db.id, name="Graph", slug="graph", description="desc"
    )
    test_db.add(graph)
    await test_db.flush()

    missing = KnowledgeNode(graph_id=graph.id, node_name="Missing", node_id_str="m1")
    outdated = KnowledgeNode(
        graph_id=graph.id,
        node_name="Outdated",
        node_id_str="o1",
        content_embedding=_vec(),
        embedding_model="old-model",
    )
    current = KnowledgeNode(
        graph_id=graph.id,
        node_name="Current",
        node_id_str="c1",
        content_embedding=_vec(),
        embedding_model=settings.GEMINI_EMBEDDING_MODEL,
    )
    test_db.add_all([missing, outdated, current])
    await test_db.commit()

    result = await get_nodes_missing_embeddings(
        test_db, graph.id, settings.GEMINI_EMBEDDING_MODEL, limit=10
    )

    result_ids = {n.id for n in result}
    assert result_ids == {missing.id, outdated.id}


@pytest.mark.asyncio
async def test_update_node_embeddings_sets_fields(test_db, user_in_db):
    graph = KnowledgeGraph(
        owner_id=user_in_db.id, name="Graph", slug="graph", description="desc"
    )
    test_db.add(graph)
    await test_db.flush()

    node_one = KnowledgeNode(
        graph_id=graph.id,
        node_name="Embed me one",
        node_id_str="e1",
    )
    node_two = KnowledgeNode(
        graph_id=graph.id,
        node_name="Embed me two",
        node_id_str="e2",
    )
    test_db.add_all([node_one, node_two])
    await test_db.commit()

    new_embedding_one = _vec(0.2)
    new_embedding_two = _vec(0.3)
    await update_node_embeddings(
        test_db,
        [(node_one.id, new_embedding_one), (node_two.id, new_embedding_two)],
        settings.GEMINI_EMBEDDING_MODEL,
    )

    updated_one = await get_node_by_id(test_db, node_one.id)
    assert updated_one is not None
    assert updated_one.embedding_model == settings.GEMINI_EMBEDDING_MODEL
    assert len(updated_one.content_embedding) == settings.GEMINI_EMBEDDING_DIM
    assert list(updated_one.content_embedding[:3]) == [0.2, 0.2, 0.2]
    assert updated_one.embedding_updated_at is not None

    updated_two = await get_node_by_id(test_db, node_two.id)
    assert updated_two is not None
    assert updated_two.embedding_model == settings.GEMINI_EMBEDDING_MODEL
    assert len(updated_two.content_embedding) == settings.GEMINI_EMBEDDING_DIM
    assert list(updated_two.content_embedding[:3]) == [0.3, 0.3, 0.3]
    assert updated_two.embedding_updated_at is not None
