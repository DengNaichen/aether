import pytest

# from app.schemas.knowledge_node import (
#     GraphStructureLLM,
#     KnowledgeNodeLLM,
#     RelationshipLLM,
# )
from app.services.ai import node_generation
from app.services.ai.node_generation import MissingAPIKeyError

# def _make_graph(nodes, relationships):
#     return GraphStructureLLM(nodes=nodes, relationships=relationships)


def test_get_client_missing_key(monkeypatch):
    monkeypatch.setattr(node_generation.settings, "GOOGLE_API_KEY", "", raising=False)
    with pytest.raises(MissingAPIKeyError, match="GOOGLE_API_KEY"):
        node_generation._get_client()


# def test_merge_graphs_dedupes_and_prefers_longer_description():
#     graph_a = _make_graph(
#         nodes=[
#             KnowledgeNodeLLM(name="Node A", description="short"),
#             KnowledgeNodeLLM(name="Node B", description="desc b"),
#         ],
#         relationships=[
#             RelationshipLLM(
#                 label="IS_PREREQUISITE_FOR",
#                 source_name="Node A",
#                 target_name="Node B",
#                 weight=1.0,
#             )
#         ],
#     )

#     graph_b = _make_graph(
#         nodes=[
#             KnowledgeNodeLLM(name="Node A", description="a much longer description"),
#             KnowledgeNodeLLM(name="Node C", description="desc c"),
#         ],
#         relationships=[
#             RelationshipLLM(
#                 label="IS_PREREQUISITE_FOR",
#                 source_name="Node A",
#                 target_name="Node B",
#                 weight=1.0,
#             ),
#             RelationshipLLM(
#                 label="IS_PREREQUISITE_FOR",
#                 source_name="Node B",
#                 target_name="Node C",
#                 weight=1.0,
#             ),
#         ],
#     )

#     merged = merge_graphs([graph_a, graph_b])

#     assert len(merged.nodes) == 3
#     merged_node_a = next(node for node in merged.nodes if node.name == "Node A")
#     assert merged_node_a.description == "a much longer description"
#     assert len(merged.relationships) == 2


# def test_process_markdown_empty_file_returns_empty_graph(tmp_path):
#     path = tmp_path / "empty.md"
#     path.write_text("", encoding="utf-8")

#     with patch(
#         "app.services.ai.generate_graph._get_client"
#     ) as mock_get_client:
#         result = process_markdown(path)

#     assert result.nodes == []
#     assert result.relationships == []
#     mock_get_client.assert_not_called()


# def test_process_markdown_extracts_merges_and_refines(tmp_path):
#     path = tmp_path / "input.md"
#     path.write_text("content", encoding="utf-8")

#     guidance_calls = []

#     def fake_extract(client, content, user_guidance=""):
#         guidance_calls.append(user_guidance)
#         if content == "chunk-1":
#             return _make_graph(
#                 nodes=[KnowledgeNodeLLM(name="Node A", description="a")],
#                 relationships=[],
#             )
#         return _make_graph(
#             nodes=[KnowledgeNodeLLM(name="Node B", description="b")],
#             relationships=[],
#         )

#     with (
#         patch("app.services.ai.generate_graph._get_client", return_value=MagicMock()),
#         patch(
#             "app.services.ai.generate_graph._create_extract_with_retry",
#             return_value=fake_extract,
#         ),
#         patch(
#             "app.services.ai.generate_graph.split_text_content",
#             return_value=["chunk-1", "chunk-2"],
#         ),
#         patch(
#             "app.services.ai.generate_graph.refine_graph_with_llm",
#             side_effect=lambda graph, *_: graph,
#         ) as mock_refine,
#     ):
#         result = process_markdown(
#             md_path=path, user_guidance="Use math", config=PipelineConfig()
#         )

#     assert len(result.nodes) == 2
#     assert any(node.name == "Node A" for node in result.nodes)
#     assert any(node.name == "Node B" for node in result.nodes)
#     assert mock_refine.called
#     assert "Use math" in guidance_calls[0]
#     assert "Processing part 1 of 2" in guidance_calls[0]
#     assert "Processing part 2 of 2" in guidance_calls[1]


# def test_process_markdown_skips_failed_chunks(tmp_path):
#     path = tmp_path / "input.md"
#     path.write_text("content", encoding="utf-8")

#     call_count = {"count": 0}

#     def fake_extract(client, content, user_guidance=""):
#         call_count["count"] += 1
#         if call_count["count"] == 1:
#             raise ValueError("boom")
#         return _make_graph(
#             nodes=[KnowledgeNodeLLM(name="Node C", description="c")],
#             relationships=[],
#         )

#     with (
#         patch("app.services.ai.generate_graph._get_client", return_value=MagicMock()),
#         patch(
#             "app.services.ai.generate_graph._create_extract_with_retry",
#             return_value=fake_extract,
#         ),
#         patch(
#             "app.services.ai.generate_graph.split_text_content",
#             return_value=["chunk-1", "chunk-2"],
#         ),
#         patch(
#             "app.services.ai.generate_graph.refine_graph_with_llm",
#             side_effect=lambda graph, *_: graph,
#         ),
#     ):
#         result = process_markdown(md_path=path, config=PipelineConfig())

#     assert len(result.nodes) == 1
#     assert result.nodes[0].name == "Node C"
