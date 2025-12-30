"""Service to detect if a PDF document is handwritten or native digital text.

This module provides heuristics to distinguish between:
1. Native digital PDFs (Latex, Word, etc.)
2. Scanned documents or Handwritten notes (iPad exports)

It analyzes text content, image coverage, and font metadata.
"""

import fitz


def is_handwritten(pdf_path: str, threshold: float = 0.15) -> bool:
    """Determines if a PDF is likely handwritten/scanned based on heuristic analysis.

    The algorithm iterates through pages to calculate a 'native ratio'.
    A page is considered 'native' if it meets criteria like:
    - Sufficient text length (>200 chars)
    - Low image coverage (unless LaTeX fonts are present)
    - Not having tiled images (slides) or single dominant images (scans)
    - Absence of known handwriting fonts (Notability, GoodNotes, etc.)

    Args:
        pdf_path: Absolute path to the PDF file.
        threshold: The ratio of native pages below which the doc is considered handwritten.
            Defaults to 0.15 (i.e., if <15% pages are native, it's handwritten).

    Returns:
        bool: True if the document is likely handwritten/scanned, False if native digital.
    """
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    if total_pages == 0:
        return False

    native_page_count = 0

    for page in doc:
        page_rect = page.rect
        page_area = page_rect.width * page_rect.height

        text = page.get_text().strip()
        text_length = len(text)

        images = page.get_image_info()

        total_image_area = 0
        for img in images:
            if "bbox" in img:
                bbox = img["bbox"]
                img_rect_area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                total_image_area += img_rect_area

        image_coverage = total_image_area / page_area if page_area > 0 else 0

        has_single_dominant_image = any(
            (img["width"] * img["height"]) > page_area * 0.7 for img in images
        )

        # Medium-sized images often indicate slide decks (tiled)
        medium_images = [
            img
            for img in images
            if 300 < img["width"] < 1500 and 300 < img["height"] < 1500
        ]
        # Heuristic: High image coverage + many medium images -> likely slides (PowerPoint export)
        is_tiled_images = len(medium_images) >= 4 and image_coverage > 0.8

        fonts = page.get_fonts()

        # Keywords indicating standard LaTeX or digital fonts
        latex_font_keywords = [
            "cm",
            "cmr",
            "cmmi",
            "cmsy",
            "cmex",
            "times",
            "helvetica",
            "courier",
            "latin",
            "lm",
            "palatino",
        ]

        # Keywords indicating handwriting apps (Notability, GoodNotes, etc.)
        handwriting_font_keywords = [
            "sfui",
            "sfns",
            "sfpro",
            "helveticaneu",
            "notability",
            "goodnotes",
        ]

        has_latex_font = any(
            any(kw in f[3].lower() for kw in latex_font_keywords) for f in fonts
        )

        has_handwriting_font = any(
            any(kw in f[3].lower() for kw in handwriting_font_keywords) for f in fonts
        )

        # A page is "native" (digital text) if:
        # 1. It has significant text content (>200 chars)
        # 2. It's not dominated by images (coverage < 0.5) UNLESS it uses LaTeX fonts (formulas are often images? No, this allows text-heavy latex docs with diagrams)
        # 3. It doesn't look like slides (tiled images)
        # 4. It doesn't look like a full page scan (single dominant image)
        # 5. It doesn't explicitly use handwriting app fonts
        is_native = (
            text_length > 200
            and (image_coverage < 0.5 or has_latex_font)
            and not is_tiled_images
            and not has_single_dominant_image
            and not has_handwriting_font
        )

        if is_native:
            native_page_count += 1

    doc.close()
    native_ratio = native_page_count / total_pages

    return native_ratio <= threshold
