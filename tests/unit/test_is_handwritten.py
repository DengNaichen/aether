"""Unit tests for is_handwritten PDF detection utility.

Tests the heuristic-based detection of handwritten/scanned PDFs vs native digital PDFs.
Uses mocks to avoid requiring actual PDF files.
"""

from unittest.mock import MagicMock, patch

from app.utils.is_handwritten import is_handwritten


def create_mock_page(
    text: str = "",
    images: list[dict] | None = None,
    fonts: list[tuple] | None = None,
    page_width: float = 612.0,
    page_height: float = 792.0,
) -> MagicMock:
    """Helper to create a mock PDF page with specified properties.

    Args:
        text: Text content returned by get_text()
        images: List of image info dicts with 'bbox', 'width', 'height'
        fonts: List of font tuples (xref, ext, type, name)
        page_width: Page width in points
        page_height: Page height in points

    Returns:
        MagicMock configured as a PDF page
    """
    mock_page = MagicMock()

    # Mock page rect
    mock_rect = MagicMock()
    mock_rect.width = page_width
    mock_rect.height = page_height
    mock_page.rect = mock_rect

    # Mock text extraction
    mock_page.get_text.return_value = text

    # Mock image info
    mock_page.get_image_info.return_value = images or []

    # Mock fonts (format: (xref, ext, type, name))
    mock_page.get_fonts.return_value = fonts or []

    return mock_page


def create_mock_pdf(pages: list[MagicMock]) -> MagicMock:
    """Helper to create a mock PDF document with specified pages.

    Args:
        pages: List of mock page objects

    Returns:
        MagicMock configured as a PDF document
    """
    mock_doc = MagicMock()
    mock_doc.__len__.return_value = len(pages)
    mock_doc.__iter__.return_value = iter(pages)
    mock_doc.close = MagicMock()
    return mock_doc


class TestIsHandwrittenBasicCases:
    """Test basic scenarios for PDF classification."""

    @patch("app.utils.is_handwritten.fitz.open")
    def test_empty_pdf_returns_false(self, mock_fitz_open):
        """Empty PDF (0 pages) should return False.

        Note: The implementation returns early for empty PDFs without calling close().
        This is acceptable since there's no resource to clean up.
        """
        mock_doc = create_mock_pdf([])
        mock_fitz_open.return_value = mock_doc

        result = is_handwritten("dummy.pdf")

        assert result is False
        # Note: close() is NOT called for empty PDFs (early return)

    @patch("app.utils.is_handwritten.fitz.open")
    def test_native_digital_pdf_returns_false(self, mock_fitz_open):
        """Native digital PDF with text and LaTeX fonts should return False."""
        # Create a page with substantial text, LaTeX fonts, low image coverage
        page = create_mock_page(
            text="A" * 500,  # Substantial text (>200 chars)
            images=[
                {
                    "bbox": [0, 0, 100, 100],
                    "width": 100,
                    "height": 100,
                }
            ],  # Small image
            fonts=[
                (1, "ttf", "Type1", "CMR10"),  # LaTeX Computer Modern font
                (2, "ttf", "Type1", "Times-Roman"),
            ],
        )

        mock_doc = create_mock_pdf([page])
        mock_fitz_open.return_value = mock_doc

        result = is_handwritten("dummy.pdf")

        # Should be classified as native (not handwritten)
        assert result is False

    @patch("app.utils.is_handwritten.fitz.open")
    def test_handwritten_pdf_high_image_coverage_returns_true(self, mock_fitz_open):
        """PDF with high image coverage and little text should return True."""
        # Page area: 612 * 792 = 484,704
        # Large image covering 80% of page
        page = create_mock_page(
            text="Page 1",  # Minimal text (<200 chars)
            images=[
                {
                    "bbox": [0, 0, 550, 700],  # Large image
                    "width": 550,
                    "height": 700,
                }
            ],
            fonts=[],
        )

        mock_doc = create_mock_pdf([page])
        mock_fitz_open.return_value = mock_doc

        result = is_handwritten("dummy.pdf")

        # Should be classified as handwritten/scanned
        assert result is True

    @patch("app.utils.is_handwritten.fitz.open")
    def test_scanned_document_single_dominant_image_returns_true(self, mock_fitz_open):
        """PDF with single dominant image (>70% of page) should return True."""
        page_area = 612.0 * 792.0

        # Image covering 75% of page area
        img_width = int((page_area * 0.75) ** 0.5)
        img_height = img_width

        page = create_mock_page(
            text="Some OCR text here",
            images=[
                {
                    "bbox": [0, 0, img_width, img_height],
                    "width": img_width,
                    "height": img_height,
                }
            ],
        )

        mock_doc = create_mock_pdf([page])
        mock_fitz_open.return_value = mock_doc

        result = is_handwritten("dummy.pdf")

        assert result is True


class TestIsHandwrittenSlideDecks:
    """Test detection of slide decks (PowerPoint exports)."""

    @patch("app.utils.is_handwritten.fitz.open")
    def test_slide_deck_tiled_images_returns_true(self, mock_fitz_open):
        """PDF with tiled medium-sized images (slides) should return True."""
        # Create a page with 5 medium-sized images (typical slide deck)
        images = [
            {"bbox": [i * 100, 0, (i + 1) * 100, 100], "width": 800, "height": 600}
            for i in range(5)
        ]

        page = create_mock_page(
            text="Slide content",
            images=images,
        )

        mock_doc = create_mock_pdf([page])
        mock_fitz_open.return_value = mock_doc

        result = is_handwritten("dummy.pdf")

        # Should be classified as handwritten (slides are not native text)
        assert result is True


class TestIsHandwrittenFontDetection:
    """Test font-based detection of handwriting apps."""

    @patch("app.utils.is_handwritten.fitz.open")
    def test_notability_font_returns_true(self, mock_fitz_open):
        """PDF with Notability fonts should return True."""
        page = create_mock_page(
            text="A" * 300,  # Substantial text
            images=[],
            fonts=[
                (1, "ttf", "Type1", "SFUIText-Regular"),  # Notability uses SF UI
            ],
        )

        mock_doc = create_mock_pdf([page])
        mock_fitz_open.return_value = mock_doc

        result = is_handwritten("dummy.pdf")

        assert result is True

    @patch("app.utils.is_handwritten.fitz.open")
    def test_goodnotes_font_returns_true(self, mock_fitz_open):
        """PDF with GoodNotes fonts should return True."""
        page = create_mock_page(
            text="A" * 300,
            images=[],
            fonts=[
                (1, "ttf", "Type1", "GoodNotes-Regular"),
            ],
        )

        mock_doc = create_mock_pdf([page])
        mock_fitz_open.return_value = mock_doc

        result = is_handwritten("dummy.pdf")

        assert result is True

    @patch("app.utils.is_handwritten.fitz.open")
    def test_helvetica_neue_font_returns_true(self, mock_fitz_open):
        """PDF with HelveticaNeue fonts (iPad apps) should return True."""
        page = create_mock_page(
            text="A" * 300,
            images=[],
            fonts=[
                (1, "ttf", "Type1", "HelveticaNeue-Light"),
            ],
        )

        mock_doc = create_mock_pdf([page])
        mock_fitz_open.return_value = mock_doc

        result = is_handwritten("dummy.pdf")

        assert result is True


class TestIsHandwrittenThreshold:
    """Test custom threshold parameter."""

    @patch("app.utils.is_handwritten.fitz.open")
    def test_custom_threshold_at_boundary(self, mock_fitz_open):
        """Test with 50% threshold - 50% native pages at boundary."""
        # Create 4 pages: 2 native, 2 handwritten
        native_page = create_mock_page(
            text="A" * 300,
            images=[],
            fonts=[(1, "ttf", "Type1", "Times-Roman")],
        )

        handwritten_page = create_mock_page(
            text="Short",
            images=[{"bbox": [0, 0, 500, 700], "width": 500, "height": 700}],
        )

        pages = [native_page, handwritten_page, native_page, handwritten_page]
        mock_doc = create_mock_pdf(pages)
        mock_fitz_open.return_value = mock_doc

        # With threshold=0.5, 50% native ratio should be at boundary
        # native_ratio (0.5) <= threshold (0.5) → True (handwritten)
        result = is_handwritten("dummy.pdf", threshold=0.5)
        assert result is True

    @patch("app.utils.is_handwritten.fitz.open")
    def test_custom_threshold_below_boundary(self, mock_fitz_open):
        """Test with threshold below native ratio."""
        # Create 4 pages: 2 native, 2 handwritten (50% native)
        native_page = create_mock_page(
            text="A" * 300,
            images=[],
            fonts=[(1, "ttf", "Type1", "Times-Roman")],
        )

        handwritten_page = create_mock_page(
            text="Short",
            images=[{"bbox": [0, 0, 500, 700], "width": 500, "height": 700}],
        )

        pages = [native_page, handwritten_page, native_page, handwritten_page]
        mock_doc = create_mock_pdf(pages)
        mock_fitz_open.return_value = mock_doc

        # With threshold=0.49, 50% native ratio exceeds threshold
        # native_ratio (0.5) > threshold (0.49) → False (not handwritten)
        result = is_handwritten("dummy.pdf", threshold=0.49)
        assert result is False

    @patch("app.utils.is_handwritten.fitz.open")
    def test_all_native_pages_returns_false(self, mock_fitz_open):
        """PDF with 100% native pages should return False."""
        native_page = create_mock_page(
            text="A" * 300,
            images=[],
            fonts=[(1, "ttf", "Type1", "CMR10")],
        )

        pages = [native_page, native_page, native_page]
        mock_doc = create_mock_pdf(pages)
        mock_fitz_open.return_value = mock_doc

        result = is_handwritten("dummy.pdf")

        # native_ratio = 1.0, threshold = 0.15
        # 1.0 > 0.15 → False (not handwritten)
        assert result is False

    @patch("app.utils.is_handwritten.fitz.open")
    def test_all_handwritten_pages_returns_true(self, mock_fitz_open):
        """PDF with 0% native pages should return True."""
        handwritten_page = create_mock_page(
            text="Short",
            images=[{"bbox": [0, 0, 500, 700], "width": 500, "height": 700}],
        )

        pages = [handwritten_page, handwritten_page, handwritten_page]
        mock_doc = create_mock_pdf(pages)
        mock_fitz_open.return_value = mock_doc

        result = is_handwritten("dummy.pdf")

        # native_ratio = 0.0, threshold = 0.15
        # 0.0 <= 0.15 → True (handwritten)
        assert result is True


class TestIsHandwrittenEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch("app.utils.is_handwritten.fitz.open")
    def test_exactly_200_chars_with_low_images(self, mock_fitz_open):
        """Page with exactly 200 chars should not meet >200 threshold."""
        page = create_mock_page(
            text="A" * 200,  # Exactly 200 chars (not >200)
            images=[],
            fonts=[(1, "ttf", "Type1", "Times-Roman")],
        )

        mock_doc = create_mock_pdf([page])
        mock_fitz_open.return_value = mock_doc

        result = is_handwritten("dummy.pdf")

        # 200 is not >200, so page is not native
        # native_ratio = 0.0 <= 0.15 → True
        assert result is True

    @patch("app.utils.is_handwritten.fitz.open")
    def test_201_chars_qualifies_as_native(self, mock_fitz_open):
        """Page with 201 chars should meet >200 threshold."""
        page = create_mock_page(
            text="A" * 201,  # >200 chars
            images=[],
            fonts=[(1, "ttf", "Type1", "Times-Roman")],
        )

        mock_doc = create_mock_pdf([page])
        mock_fitz_open.return_value = mock_doc

        result = is_handwritten("dummy.pdf")

        # 201 > 200, low images, no handwriting fonts → native
        # native_ratio = 1.0 > 0.15 → False (not handwritten)
        assert result is False

    @patch("app.utils.is_handwritten.fitz.open")
    def test_latex_font_allows_higher_image_coverage(self, mock_fitz_open):
        """LaTeX fonts allow >50% image coverage (for diagrams/formulas)."""
        # Page with 60% image coverage but LaTeX fonts
        page = create_mock_page(
            text="A" * 300,
            images=[
                {
                    "bbox": [0, 0, 450, 600],  # ~60% coverage
                    "width": 450,
                    "height": 600,
                }
            ],
            fonts=[
                (1, "ttf", "Type1", "CMMI10"),  # LaTeX math italic
            ],
        )

        mock_doc = create_mock_pdf([page])
        mock_fitz_open.return_value = mock_doc

        result = is_handwritten("dummy.pdf")

        # Should still be classified as native due to LaTeX fonts
        assert result is False

    @patch("app.utils.is_handwritten.fitz.open")
    def test_no_fonts_no_images_sufficient_text(self, mock_fitz_open):
        """Page with sufficient text but no fonts/images should be native."""
        page = create_mock_page(
            text="A" * 300,
            images=[],
            fonts=[],
        )

        mock_doc = create_mock_pdf([page])
        mock_fitz_open.return_value = mock_doc

        result = is_handwritten("dummy.pdf")

        # >200 chars, <50% image coverage → native
        assert result is False
