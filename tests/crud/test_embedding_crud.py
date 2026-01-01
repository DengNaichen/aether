import pytest

from app.core.config import settings
from app.crud.knowledge_node import (
    get_node_by_id,
    get_nodes_missing_embeddings,
    update_node_embedding,
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
async def test_update_node_embedding_sets_fields(test_db, user_in_db):
    graph = KnowledgeGraph(
        owner_id=user_in_db.id, name="Graph", slug="graph", description="desc"
    )
    test_db.add(graph)
    await test_db.flush()

    node = KnowledgeNode(
        graph_id=graph.id,
        node_name="Embed me",
        node_id_str="e1",
    )
    test_db.add(node)
    await test_db.commit()

    new_embedding = _vec(0.2)
    await update_node_embedding(
        test_db, node.id, new_embedding, settings.GEMINI_EMBEDDING_MODEL
    )

    updated = await get_node_by_id(test_db, node.id)
    assert updated is not None
    assert updated.embedding_model == settings.GEMINI_EMBEDDING_MODEL
    assert len(updated.content_embedding) == settings.GEMINI_EMBEDDING_DIM
    assert list(updated.content_embedding[:3]) == [0.2, 0.2, 0.2]
