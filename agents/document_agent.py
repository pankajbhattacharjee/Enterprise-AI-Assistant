from sqlalchemy.orm import Session
from backend.services import answer_with_llm
from rag.pipeline import retrieve


def run(question: str, user_id: int, db: Session) -> dict:
    chunks = retrieve(question, user_id)
    context = "\n\n".join(f"[{item['document']} p.{item.get('page') or 'n/a'}] {item['text']}" for item in chunks)
    citations = [{"document": item["document"], "page": item.get("page"), "score": item["score"], "excerpt": item["text"][:260]} for item in chunks]
    return {"answer": answer_with_llm(question, context), "confidence": chunks[0]["score"] if chunks else 0.0, "citations": citations}
