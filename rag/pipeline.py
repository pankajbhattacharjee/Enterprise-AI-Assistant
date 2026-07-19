from pathlib import Path
from rag.loader import extract_text
from rag.splitter import split_text
from rag.vectorstore import LocalVectorStore


def index_document(path: Path, document_id: int, owner_id: int, filename: str) -> int:
    records = []
    for page, text in extract_text(path):
        for chunk in split_text(text):
            records.append({"document_id": document_id, "owner_id": owner_id, "document": filename, "page": page, "text": chunk})
    return LocalVectorStore().add(records)


def retrieve(question: str, owner_id: int) -> list[dict]:
    return LocalVectorStore().search(question, owner_id)
