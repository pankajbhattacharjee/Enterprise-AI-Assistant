import logging
from google import genai
from backend.config import get_settings

logger = logging.getLogger(__name__)


def answer_with_llm(question: str, context: str) -> str:
    """Ground a Gemini response in retrieved content; never expose chunks as an answer."""
    settings = get_settings()
    if not context.strip():
        logger.info("RAG_GENERATION skipped: no retrieved context")
        return "I could not find relevant information in your indexed documents."

    api_key = (settings.gemini_api_key or "").strip()
    if not api_key:
        logger.warning("RAG_GENERATION unavailable: GEMINI_API_KEY is not configured")
        return "I found relevant document content, but no Gemini API key is configured to generate an answer. Add GEMINI_API_KEY to .env and restart the API."

    try:
        logger.info("RAG_GENERATION calling Gemini model=%s context_chars=%d", settings.gemini_model, len(context))
        client = genai.Client(api_key=api_key)
        prompt = f"""You are an enterprise assistant. Write a direct, professional answer to the employee's question using only the supplied document context.

Rules:
- Synthesize the answer; never paste raw chunks or mention retrieval.
- Include exact quantities, categories, conditions, and limits when stated.
- If the answer is absent or ambiguous, say that clearly instead of guessing.
- Use one concise paragraph. Do not include a Sources heading; citations are added by the application.

Employee question: {question}

Document context:
{context}"""
        response = client.models.generate_content(model=settings.gemini_model, contents=prompt)
        answer = (response.text or "").strip()
        if not answer:
            raise RuntimeError("Gemini returned an empty response")
        logger.info("RAG_GENERATION Gemini success answer_chars=%d", len(answer))
        return answer
    except Exception as exc:
        logger.exception("RAG_GENERATION Gemini failed; answer generation unavailable")
        # The provider message contains status details (for example 401, 403,
        # 404, or quota exhaustion) but never includes the API key.
        provider_detail = " ".join(str(exc).split())[:500]
        return f"Gemini could not generate an answer ({type(exc).__name__}: {provider_detail}). Check the model, API key restrictions, quota, and API access for this project."
