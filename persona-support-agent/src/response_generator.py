"""
Adaptive response generator — generates persona-specific responses grounded in
retrieved knowledge base chunks using Gemini.
"""
from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY, LLM_MODEL
from src.prompts import PERSONA_PROMPTS
from src.utils import call_with_backoff, format_sources


def generate_response(
    query: str,
    persona: str,
    chunks: list[dict],
    conversation_history: list[dict] | None = None,
) -> dict:
    """
    Generate a persona-adaptive response grounded in retrieved chunks.

    Args:
        query: The user's current question.
        persona: Detected persona ("Technical Expert", "Frustrated User", "Business Executive").
        chunks: Retrieved document chunks [{text, source, score, ...}, ...].
        conversation_history: Optional list of recent messages for context.

    Returns:
        dict with keys:
            - response: str  (the generated answer)
            - sources: list[str]  (source filenames cited)
    """
    client = genai.Client(api_key=GEMINI_API_KEY)

    # Select persona-specific system prompt
    system_prompt = PERSONA_PROMPTS.get(persona, PERSONA_PROMPTS["Technical Expert"])

    # Build context block from retrieved chunks
    if chunks:
        context_parts = []
        for i, chunk in enumerate(chunks, start=1):
            source = chunk.get("source", "unknown")
            score = chunk.get("score", 0.0)
            text = chunk.get("text", "")
            page = chunk.get("page", "")
            page_info = f", Page {page}" if page and page != "1" else ""
            context_parts.append(
                f"[Document {i} | Source: {source}{page_info} | Relevance: {score:.0%}]\n{text}"
            )
        context_block = "\n\n---\n\n".join(context_parts)
    else:
        context_block = "No relevant documents were found in the knowledge base."

    # Build conversation history block
    history_block = ""
    if conversation_history:
        lines = []
        for msg in conversation_history[-5:]:
            role = "User" if msg["role"] == "user" else "Support Agent"
            lines.append(f"{role}: {msg['content']}")
        if lines:
            history_block = (
                "\n--- Recent Conversation History ---\n"
                + "\n".join(lines)
                + "\n--- End History ---\n\n"
            )

    # Compose the full prompt
    user_prompt = (
        f"{history_block}"
        f"CONTEXT DOCUMENTS:\n\n{context_block}\n\n"
        f"---\n\n"
        f"Customer Question: {query}"
    )

    def _call():
        return client.models.generate_content(
            model=LLM_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.3,
                max_output_tokens=1024,
            ),
        )

    response_obj = call_with_backoff(_call)
    response_text = response_obj.text.strip()

    sources = format_sources(chunks)

    return {
        "response": response_text,
        "sources": sources,
    }
