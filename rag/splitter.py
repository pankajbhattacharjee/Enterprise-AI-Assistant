def split_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    """Split on word boundaries while preserving a small retrieval overlap."""
    words = text.split()
    if not words:
        return []
    chunks, start = [], 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = max(start + 1, end - overlap)
    return chunks
