import shutil

import pytest

from app.utils.storage import RESULTS_BASE, STORAGE_BASE


@pytest.fixture
def cleanup_storage():
    yield
    if STORAGE_BASE.exists():
        shutil.rmtree(STORAGE_BASE)
    if RESULTS_BASE.exists():
        shutil.rmtree(RESULTS_BASE)


# class TestUploadFileEndpoint:
#     @pytest.mark.asyncio
#     async def test_upload_file_rejects_invalid_extension(
#         self, authenticated_client, private_graph_in_db
#     ):
#         response = await authenticated_client.post(
#             f"/me/graphs/{private_graph_in_db.id}/upload-file",
#             files={"file": ("test.txt", b"not a pdf", "text/plain")},
#         )

#         assert response.status_code == 400
#         assert "Only PDF (.pdf) and Markdown (.md) files are supported." in response.json()[
#             "detail"
#         ]

#     @pytest.mark.asyncio
#     async def test_upload_file_conflict_when_graph_has_nodes(
#         self, authenticated_client, private_graph_in_db, test_db
#     ):
#         node = KnowledgeNode(
#             graph_id=private_graph_in_db.id,
#             node_name="Existing Node",
#         )
#         test_db.add(node)
#         await test_db.commit()

#         response = await authenticated_client.post(
#             f"/me/graphs/{private_graph_in_db.id}/upload-file",
#             files={"file": ("test.md", b"# Title", "text/markdown")},
#         )

#         assert response.status_code == 409
#         assert (
#             "Graph already has data. Incremental updates are not enabled yet."
#             in response.json()["detail"]
#         )

#     @pytest.mark.asyncio
#     async def test_upload_file_pdf_success(
#         self, authenticated_client, private_graph_in_db, cleanup_storage
#     ):
#         graph_stats = {
#             "nodes_created": 2,
#             "prerequisites_created": 1,
#             "total_nodes": 2,
#             "max_level": 1,
#         }

#         with patch(
#             "app.routes.my_graphs.PDFPipeline.execute",
#             new=AsyncMock(return_value={"graph_stats": graph_stats}),
#         ):
#             response = await authenticated_client.post(
#                 f"/me/graphs/{private_graph_in_db.id}/upload-file",
#                 files={"file": ("test.pdf", b"%PDF-1.4 test", "application/pdf")},
#             )

#         assert response.status_code == 201
#         data = response.json()
#         assert data["graph_id"] == str(private_graph_in_db.id)
#         assert data["nodes_created"] == graph_stats["nodes_created"]
#         assert data["prerequisites_created"] == graph_stats["prerequisites_created"]
#         assert data["total_nodes"] == graph_stats["total_nodes"]
#         assert data["max_level"] == graph_stats["max_level"]

#     @pytest.mark.asyncio
#     async def test_upload_file_markdown_success(
#         self, authenticated_client, private_graph_in_db
#     ):
#         graph_stats = {
#             "nodes_created": 1,
#             "prerequisites_created": 0,
#             "total_nodes": 1,
#             "max_level": 0,
#         }

#         with patch(
#             "app.services.graph_generation_service.GraphGenerationService.create_graph_from_markdown",
#             new=AsyncMock(return_value=graph_stats),
#         ) as mock_create:
#             response = await authenticated_client.post(
#                 f"/me/graphs/{private_graph_in_db.id}/upload-file",
#                 files={
#                     "file": ("test.md", b"# Intro\n\nContent", "text/markdown")
#                 },
#             )

#         assert response.status_code == 201
#         data = response.json()
#         assert data["graph_id"] == str(private_graph_in_db.id)
#         assert data["nodes_created"] == graph_stats["nodes_created"]
#         assert data["prerequisites_created"] == graph_stats["prerequisites_created"]
#         assert data["total_nodes"] == graph_stats["total_nodes"]
#         assert data["max_level"] == graph_stats["max_level"]
#         mock_create.assert_awaited_once_with(
#             graph_id=private_graph_in_db.id,
#             markdown_content="# Intro\n\nContent",
#             incremental=False,
#         )

#     @pytest.mark.asyncio
#     async def test_upload_file_markdown_invalid_encoding(
#         self, authenticated_client, private_graph_in_db
#     ):
#         response = await authenticated_client.post(
#             f"/me/graphs/{private_graph_in_db.id}/upload-file",
#             files={"file": ("bad.md", b"\xff", "text/markdown")},
#         )

#         assert response.status_code == 400
#         assert "Invalid file encoding" in response.json()["detail"]
