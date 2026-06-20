"""
Escalation engine — determines when to escalate to human support and
generates a structured handoff JSON summary.
"""
import json
from google import genai
from google.genai import types

from src.config import (
    GEMINI_API_KEY,
    LLM_MODEL,
    ESCALATION_SCORE_THRESHOLD,
    ESCALATION_DISSATISFACTION_COUNT,
    ESCALATION_KEYWORDS,
    DISSATISFACTION_SIGNALS,
)
from src.prompts import HANDOFF_SYSTEM_PROMPT
from src.utils import call_with_backoff


def check_escalation(
    chunks: list[dict],
    dissatisfaction_count: int,
    query: str,
    custom_score_threshold: float | None = None,
    custom_dissatisfaction_threshold: int | None = None,
    custom_keywords: list[str] | None = None,
) -> dict:
    """
    Evaluate whether the current interaction should be escalated to a human agent.

    Args:
        chunks: Retrieved document chunks with scores.
        dissatisfaction_count: Number of times user has shown dissatisfaction in session.
        query: The current user message.
        custom_score_threshold: Override for score threshold (config default used if None).
        custom_dissatisfaction_threshold: Override for dissatisfaction count threshold.
        custom_keywords: Override for escalation keywords list.

    Returns:
        dict with keys:
            - should_escalate: bool
            - reason: str  (human-readable explanation)
            - trigger: str  (machine-readable trigger name)
    """
    score_threshold = custom_score_threshold or ESCALATION_SCORE_THRESHOLD
    dissatisfaction_threshold = custom_dissatisfaction_threshold or ESCALATION_DISSATISFACTION_COUNT
    keywords = custom_keywords if custom_keywords is not None else ESCALATION_KEYWORDS

    query_lower = query.lower()

    # 1. No documents retrieved
    if not chunks:
        return {
            "should_escalate": True,
            "reason": "No relevant documents were found in the knowledge base to answer this query.",
            "trigger": "no_documents",
        }

    # 2. Low retrieval confidence
    best_score = max(c.get("score", 0.0) for c in chunks)
    if best_score < score_threshold:
        return {
            "should_escalate": True,
            "reason": (
                f"Retrieval confidence is too low (best score: {best_score:.2f}, "
                f"threshold: {score_threshold:.2f}). Cannot provide a reliable answer."
            ),
            "trigger": "low_confidence",
        }

    # 3. Sensitive keyword detected
    for kw in keywords:
        if kw.lower() in query_lower:
            return {
                "should_escalate": True,
                "reason": (
                    f"Query contains a sensitive keyword '{kw}' that requires human review "
                    "(billing, legal, or account-sensitive matter)."
                ),
                "trigger": "sensitive_keyword",
            }

    # 4. Repeated dissatisfaction
    if dissatisfaction_count >= dissatisfaction_threshold:
        return {
            "should_escalate": True,
            "reason": (
                f"User has expressed dissatisfaction {dissatisfaction_count} time(s) "
                f"(threshold: {dissatisfaction_threshold}). Escalating for human assistance."
            ),
            "trigger": "repeated_dissatisfaction",
        }

    return {"should_escalate": False, "reason": "", "trigger": ""}


def detect_dissatisfaction(message: str) -> bool:
    """
    Check if a message contains dissatisfaction signals.

    Args:
        message: The user's message.

    Returns:
        True if dissatisfaction signals are detected.
    """
    message_lower = message.lower()
    return any(signal in message_lower for signal in DISSATISFACTION_SIGNALS)


def generate_handoff(
    persona: str,
    query: str,
    conversation_history: list[dict],
    chunks: list[dict],
    attempted_steps: list[str],
    escalation_reason: str,
) -> dict:
    """
    Generate a structured human handoff summary using Gemini.

    Args:
        persona: Detected persona.
        query: The user's current query.
        conversation_history: Full conversation history list.
        chunks: Retrieved document chunks.
        attempted_steps: List of steps that were tried.
        escalation_reason: Why escalation was triggered.

    Returns:
        Structured handoff dict matching the required schema.
    """
    client = genai.Client(api_key=GEMINI_API_KEY)

    # Build a prompt for Gemini to generate the recommendation
    history_text = ""
    if conversation_history:
        lines = []
        for msg in conversation_history[-10:]:
            role = "User" if msg["role"] == "user" else "Agent"
            lines.append(f"{role}: {msg['content']}")
        history_text = "\n".join(lines)

    docs_used = list({c.get("source", "unknown") for c in chunks})
    best_score = max((c.get("score", 0.0) for c in chunks), default=0.0)

    prompt = (
        f"A customer support case requires human escalation.\n\n"
        f"Persona: {persona}\n"
        f"Escalation Reason: {escalation_reason}\n"
        f"Current User Query: {query}\n"
        f"Confidence Score: {best_score:.2f}\n\n"
        f"Conversation History:\n{history_text or 'No prior history.'}\n\n"
        f"Documents retrieved: {', '.join(docs_used) or 'None'}\n\n"
        f"Generate a professional 2-3 sentence recommendation for the human support agent "
        f"covering: what to investigate, what the customer needs, and the urgency level."
    )

    def _call():
        return client.models.generate_content(
            model=LLM_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=HANDOFF_SYSTEM_PROMPT,
                temperature=0.2,
                max_output_tokens=300,
            ),
        )

    try:
        rec_response = call_with_backoff(_call)
        recommendation = rec_response.text.strip()
    except Exception:
        recommendation = (
            "Please review the full conversation history and address the customer's "
            "concern with priority. Verify their account status and provide direct assistance."
        )

    # Build the structured handoff JSON
    handoff = {
        "persona": persona,
        "issue": query[:300] + ("..." if len(query) > 300 else ""),
        "escalation_reason": escalation_reason,
        "conversation_history": [
            {"role": msg["role"], "content": msg["content"][:500]}
            for msg in conversation_history[-10:]
        ],
        "documents_used": docs_used,
        "attempted_steps": attempted_steps,
        "recommendation": recommendation,
        "confidence_score": round(best_score, 4),
    }

    return handoff
