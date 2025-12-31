def split_text_content(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Splits text into chunks, trying to preserve logical boundaries (headers).
    This is a simplified splitter that prioritizes splitting at logical sections.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size

        # If this is the last chunk, just take it
        if end >= text_len:
            chunks.append(text[start:])
            break

        # Try to find a good break point (header) within the last 10% of the chunk
        # scan backwards from 'end'
        search_start = max(start, end - int(chunk_size * 0.2))
        slice_to_search = text[search_start:end]

        # Priority 1: Main headers
        last_break = slice_to_search.rfind("\n# ")
        if last_break == -1:
            # Priority 2: Sub headers
            last_break = slice_to_search.rfind("\n## ")

        if last_break != -1:
            # Found a header to break on
            actual_end = search_start + last_break
        else:
            # Fallback: finding the last paragraph break
            last_para = slice_to_search.rfind("\n\n")
            if last_para != -1:
                actual_end = search_start + last_para
            else:
                # Hard break
                actual_end = end

        # Ensure we make progress
        if actual_end <= start:
            actual_end = end

        chunk = text[start:actual_end]
        chunks.append(chunk)

        # Move start, accounting for overlap if we aren't at the very end
        # But for graph extraction, 'overlap' might just mean redundant context.
        # Simple approach: raw overlap.
        start = max(start + 1, actual_end - overlap)

    return chunks
