"""
Classifier module — detects customer persona using Gemini structured outputs.
"""
import json
import os
from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY, LLM_MODEL
from src.utils import call_with_backoff


# ─── Schema ───────────────────────────────────────────────────────────────────
_PERSONA_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "persona": {
            "type": "STRING",
            "enum": ["Technical Expert", "Frustrated User", "Business Executive"],
        },
        "confidence": {"type": "NUMBER"},
        "reasoning": {"type": "STRING"},
    },
    "required": ["persona", "confidence", "reasoning"],
}

_SYSTEM_INSTRUCTION = (
    "You are an advanced customer persona classification engine.\n"
    "Analyze the user's message (and conversation history if provided) and classify "
    "it into EXACTLY ONE of these three customer personas:\n\n"
    "1. 'Technical Expert'\n"
    "   - Uses technical terminology (APIs, logs, configs, error codes, stack traces)\n"
    "   - Asks about implementation details, root causes, debugging steps\n"
    "   - Wants detailed technical explanations and precise information\n\n"
    "2. 'Frustrated User'\n"
    "   - Expresses emotional language, frustration, anger, or despair\n"
    "   - Uses exclamation marks, repetition, or urgent language\n"
    "   - Mentions repeated failed attempts or lack of progress\n\n"
    "3. 'Business Executive'\n"
    "   - Focuses on business outcomes, operational impact, ROI, timelines\n"
    "   - Prefers concise, high-level communication without technical jargon\n"
    "   - Asks about SLAs, resolution times, and business consequences\n\n"
    "Return your evaluation in the required JSON structure. "
    "Confidence should be between 0.0 and 1.0."
)


def classify_persona(user_message: str, conversation_history: list[dict] | None = None) -> dict:
    """
    Classify the user's persona from the message and optional conversation history.

    Args:
        user_message: The current user message.
        conversation_history: Optional list of recent messages for context.
                              Each item: {"role": "user"|"assistant", "content": str}

    Returns:
        dict with keys: persona (str), confidence (float), reasoning (str)
    """
    client = genai.Client(api_key=GEMINI_API_KEY)

    # Build context block from history
    history_text = ""
    if conversation_history:
        history_lines = []
        for msg in conversation_history[-5:]:  # last 5 turns
            role = msg.get("role", "user").capitalize()
            content = msg.get("content", "")
            history_lines.append(f"{role}: {content}")
        if history_lines:
            history_text = (
                "\n\n--- Conversation History (for context) ---\n"
                + "\n".join(history_lines)
                + "\n--- End of History ---\n\n"
            )

    prompt = f"{history_text}Current User Message:\n{user_message}"

    def _call():
        return client.models.generate_content(
            model=LLM_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=_PERSONA_SCHEMA,
                temperature=0.1,
            ),
        )

    response = call_with_backoff(_call)
    result = json.loads(response.text)

    # Normalise confidence to [0, 1]
    result["confidence"] = max(0.0, min(1.0, float(result.get("confidence", 0.5))))
    return result
