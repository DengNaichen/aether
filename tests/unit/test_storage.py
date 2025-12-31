import os
import shutil
from pathlib import Path

from app.utils.storage import (
    RESULTS_BASE,
    STORAGE_BASE,
    cleanup_task_storage,
    get_task_storage_path,
    save_task_markdown,
    save_upload_file,
)


class TestStorageConfiguration:
    """Tests for storage configuration and path management."""

    def test_storage_base_is_configurable(self):
        """Verify STORAGE_BASE uses settings, not hardcoded path."""
        assert isinstance(STORAGE_BASE, Path)
        # Should be relative path from config default
        assert "temp/pipeline_storage" in str(STORAGE_BASE)

    def test_results_base_is_configurable(self):
        """Verify RESULTS_BASE uses settings, not hardcoded path."""
        assert isinstance(RESULTS_BASE, Path)
        # Should be relative path from config default
        assert "temp/results" in str(RESULTS_BASE)


class TestTaskStoragePath:
    """Tests for get_task_storage_path function."""

    def test_get_task_storage_path_creates_directory(self):
        """Should create task directory if it doesn't exist."""
        task_id = "12345"
        path = get_task_storage_path(task_id)

        assert path.exists()
        assert path.is_dir()
        assert f"task_{task_id}" in str(path)

        # Cleanup
        cleanup_task_storage(task_id)

    def test_get_task_storage_path_idempotent(self):
        """Should return same path on multiple calls."""
        task_id = "12346"
        path1 = get_task_storage_path(task_id)
        path2 = get_task_storage_path(task_id)

        assert path1 == path2
        assert path1.exists()

        # Cleanup
        cleanup_task_storage(task_id)


class TestSaveUploadFile:
    """Tests for save_upload_file function."""

    def test_save_upload_file_success(self):
        """Should save file with standardized name."""
        task_id = "999"
        content = b"fake pdf content"
        original_filename = "test.pdf"

        path = save_upload_file(task_id, original_filename, content)

        assert os.path.exists(path)
        assert path.endswith("input.pdf")  # Standardized name
        assert f"task_{task_id}" in path

        # Verify content
        with open(path, "rb") as f:
            assert f.read() == content

        # Cleanup
        cleanup_task_storage(task_id)

    def test_save_upload_file_overwrites_existing(self):
        """Should overwrite if file already exists."""
        task_id = "1000"
        content1 = b"first content"
        content2 = b"second content"

        path1 = save_upload_file(task_id, "test1.pdf", content1)
        path2 = save_upload_file(task_id, "test2.pdf", content2)

        # Same path (standardized to input.pdf)
        assert path1 == path2

        # Should have second content
        with open(path2, "rb") as f:
            assert f.read() == content2

        # Cleanup
        cleanup_task_storage(task_id)


class TestSaveTaskMarkdown:
    """Tests for save_task_markdown function."""

    def test_save_task_markdown_success(self):
        """Should save markdown content to results directory."""
        task_id = "2000"
        content = "# Test Markdown\n\nSome content here."

        try:
            path = save_task_markdown(task_id, content)

            assert os.path.exists(path)
            assert f"task_{task_id}_content.md" in path
            assert str(RESULTS_BASE) in path

            # Verify content
            with open(path, encoding="utf-8") as f:
                assert f.read() == content

        finally:
            # Cleanup results directory
            if RESULTS_BASE.exists():
                shutil.rmtree(RESULTS_BASE)

    def test_save_task_markdown_creates_results_dir(self):
        """Should create RESULTS_BASE if it doesn't exist."""
        task_id = "2001"

        # Ensure results dir doesn't exist
        if RESULTS_BASE.exists():
            shutil.rmtree(RESULTS_BASE)

        try:
            path = save_task_markdown(task_id, "test content")

            assert RESULTS_BASE.exists()
            assert os.path.exists(path)

        finally:
            if RESULTS_BASE.exists():
                shutil.rmtree(RESULTS_BASE)


class TestCleanupTaskStorage:
    """Tests for cleanup_task_storage function."""

    def test_cleanup_removes_task_directory(self):
        """Should remove entire task directory."""
        task_id = "3000"
        content = b"test content"

        # Create task with file
        path = save_upload_file(task_id, "test.pdf", content)
        assert os.path.exists(path)
        task_dir = os.path.dirname(path)
        assert os.path.exists(task_dir)

        # Cleanup
        cleanup_task_storage(task_id)

        # Verify removal
        assert not os.path.exists(path)
        assert not os.path.exists(task_dir)

    def test_cleanup_handles_nonexistent_task(self):
        """Should not raise error if task doesn't exist."""
        task_id = "9999999"
        # Should not raise
        cleanup_task_storage(task_id)

    def test_cleanup_removes_all_files_in_task(self):
        """Should remove all files in task directory."""
        task_id = "3001"

        # Create task directory with multiple files
        task_dir = get_task_storage_path(task_id)
        file1 = task_dir / "file1.txt"
        file2 = task_dir / "file2.txt"
        subdir = task_dir / "subdir"
        subdir.mkdir()
        file3 = subdir / "file3.txt"

        file1.write_text("content1")
        file2.write_text("content2")
        file3.write_text("content3")

        assert file1.exists()
        assert file2.exists()
        assert file3.exists()

        # Cleanup
        cleanup_task_storage(task_id)

        # All should be removed
        assert not task_dir.exists()
        assert not file1.exists()
        assert not file2.exists()
        assert not subdir.exists()


class TestStorageIntegration:
    """Integration tests for storage workflow."""

    def test_full_storage_workflow(self):
        """Test complete workflow: save upload -> save markdown -> cleanup."""
        task_id = "4000"

        try:
            # 1. Save uploaded file
            pdf_content = b"%PDF-1.4 fake pdf"
            pdf_path = save_upload_file(task_id, "original.pdf", pdf_content)
            assert os.path.exists(pdf_path)

            # 2. Save markdown result
            markdown_content = "# Extracted Content\n\nSome text."
            md_path = save_task_markdown(task_id, markdown_content)
            assert os.path.exists(md_path)

            # 3. Verify both exist
            assert os.path.exists(pdf_path)
            assert os.path.exists(md_path)

            # 4. Cleanup task storage (not results)
            cleanup_task_storage(task_id)

            # 5. Task storage should be gone, but results should remain
            assert not os.path.exists(pdf_path)
            assert os.path.exists(md_path)  # Results persist

        finally:
            # Final cleanup
            cleanup_task_storage(task_id)
            if RESULTS_BASE.exists():
                shutil.rmtree(RESULTS_BASE)
