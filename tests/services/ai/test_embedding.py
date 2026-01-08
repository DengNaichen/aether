import pytest

from app.core.config import settings
from app.crud import knowledge_node
from app.models.knowledge_graph import KnowledgeGraph
from app.models.knowledge_node import KnowledgeNode
from app.services.ai.embedding import EmbeddingService


def _vec(val: float = 0.05) -> list[float]:
    return [val] * settings.GEMINI_EMBEDDING_DIM


@pytest.mark.asyncio
async def test_embed_graph_nodes(monkeypatch, test_db, user_in_db):
    graph = KnowledgeGraph(
        owner_id=user_in_db.id, name="Graph", slug="graph", description="desc"
    )
    test_db.add(graph)
    await test_db.flush()

    to_embed = KnowledgeNode(
        graph_id=graph.id,
        node_name="Node A",
        node_id_str="a",
        description="some description",
    )
    already_embedded = KnowledgeNode(
        graph_id=graph.id,
        node_name="Node B",
        node_id_str="b",
        content_embedding=_vec(0.9),
        embedding_model=settings.GEMINI_EMBEDDING_MODEL,
    )
    empty_content = KnowledgeNode(
        graph_id=graph.id,
        node_name="",
        node_id_str="c",
        description=None,
    )

    test_db.add_all([to_embed, already_embedded, empty_content])
    await test_db.commit()

    async def fake_embed_text(self, text: str):
        return _vec()

    monkeypatch.setattr(EmbeddingService, "_embed_text", fake_embed_text)

    service = EmbeddingService(test_db)
    result = await service.embed_graph_nodes(graph.id, batch_size=10)

    assert result["embedded"] == 1
    assert result["skipped_empty"] == 1

    updated = await knowledge_node.get_node_by_id(test_db, to_embed.id)
    assert updated is not None
    assert updated.embedding_model == settings.GEMINI_EMBEDDING_MODEL
    assert len(updated.content_embedding) == settings.GEMINI_EMBEDDING_DIM
