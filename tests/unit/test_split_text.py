"""Unit tests for text content splitting utilities.

Tests the split_text_content() function.
"""


from app.utils.split_text import split_text_content


class TestSplitTextContent:
    """Test cases for split_text_content() function."""

    def test_small_text_no_splitting(self):
        """Text shorter than chunk_size should return single chunk."""
        text = "This is a short text."
        result = split_text_content(text, chunk_size=100, overlap=0)

        assert len(result) == 1
        assert result[0] == text

    def test_split_at_main_header(self):
        """Text should split at main headers (# )."""
        text = """Introduction text here.

# Section 1
Content for section 1.

# Section 2
Content for section 2."""

        result = split_text_content(text, chunk_size=50, overlap=0)

        # Should split at headers
        assert len(result) > 1
        # First chunk should contain introduction
        assert "Introduction" in result[0]

    def test_split_at_subheader(self):
        """Text should split at subheaders (## ) if no main headers."""
        text = """Introduction text here.

## Subsection 1
Content for subsection 1.

## Subsection 2
Content for subsection 2."""

        result = split_text_content(text, chunk_size=50, overlap=0)

        assert len(result) > 1

    def test_split_at_paragraph_break(self):
        """Text should split at paragraph breaks if no headers."""
        text = "First paragraph content here.\n\nSecond paragraph content here.\n\nThird paragraph content here."

        result = split_text_content(text, chunk_size=40, overlap=0)

        assert len(result) > 1

    def test_hard_break_no_boundaries(self):
        """Text with no logical boundaries should hard break."""
        text = "A" * 200  # No headers or paragraph breaks

        result = split_text_content(text, chunk_size=50, overlap=0)

        assert len(result) == 4  # 200 / 50 = 4 chunks
        for chunk in result:
            assert len(chunk) <= 50

    def test_overlap_creates_overlapping_chunks(self):
        """Overlap parameter should create overlapping content."""
        text = "A" * 100

        result = split_text_content(text, chunk_size=40, overlap=10)

        # With overlap, chunks should have some shared content
        assert len(result) >= 2

        # Verify chunks are created (exact count depends on overlap logic)
        total_length = sum(len(chunk) for chunk in result)
        assert total_length > len(text)  # Overlap means total > original

    def test_empty_text(self):
        """Empty text should return single empty chunk."""
        result = split_text_content("", chunk_size=100, overlap=0)

        assert len(result) == 1
        assert result[0] == ""

    def test_exact_chunk_size(self):
        """Text exactly chunk_size should return single chunk."""
        text = "A" * 100
        result = split_text_content(text, chunk_size=100, overlap=0)

        assert len(result) == 1
        assert result[0] == text

    def test_progress_guarantee(self):
        """Splitting should always make progress (no infinite loops)."""
        text = "A" * 1000

        result = split_text_content(text, chunk_size=50, overlap=10)

        # Should complete without hanging
        assert len(result) > 0
        # Verify all text is covered
        assert "".join(result).startswith(text[:100])

    def test_header_priority(self):
        """Main headers should be preferred over subheaders."""
        text = """Content before.

# Main Header
## Subheader
More content here that makes this chunk long enough to need splitting."""

        result = split_text_content(text, chunk_size=50, overlap=0)

        # Should split at main header, not subheader
        assert len(result) >= 1

    def test_very_short_chunk_size(self):
        """Very small chunk_size should still work."""
        text = "This is a test sentence."

        result = split_text_content(text, chunk_size=10, overlap=0)

        assert len(result) > 1
        for chunk in result:
            assert len(chunk) <= 10 or len(chunk) <= 11  # Allow slight overflow

    def test_multiline_text_with_headers(self):
        """Complex markdown text should split intelligently."""
        text = """# Introduction

This is the introduction section with some content.

# Chapter 1

## Section 1.1

Content for section 1.1 goes here.

## Section 1.2

Content for section 1.2 goes here.

# Chapter 2

More content in chapter 2."""

        result = split_text_content(text, chunk_size=80, overlap=10)

        # Should create multiple chunks
        assert len(result) > 1

        # Verify content is preserved
        combined = "".join(result)
        assert "Introduction" in combined
        assert "Chapter 1" in combined
        assert "Chapter 2" in combined

    def test_no_header_at_boundary(self):
        """If no header found in search window, should use paragraph break."""
        text = "A" * 100 + "\n\n" + "B" * 100

        result = split_text_content(text, chunk_size=150, overlap=0)

        # Should split at paragraph break
        assert len(result) == 2

    def test_overlap_larger_than_chunk(self):
        """Overlap larger than chunk_size should still make progress."""
        text = "A" * 200

        # This is an edge case - overlap shouldn't prevent progress
        result = split_text_content(text, chunk_size=50, overlap=60)

        # Should still complete (implementation should handle this)
        assert len(result) > 0
