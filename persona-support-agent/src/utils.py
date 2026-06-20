"""
Utility functions: exponential backoff, analytics tracker, text helpers.
"""
import time
import random
from collections import defaultdict
from dataclasses import dataclass, field


# ─── Retry / Backoff ─────────────────────────────────────────────────────────

def call_with_backoff(func, max_retries: int = 5):
    """
    Call a zero-argument callable with exponential backoff on failure.

    Args:
        func: A callable that takes no arguments.
        max_retries: Maximum number of retry attempts.

    Returns:
        The return value of the callable on success.

    Raises:
        The last exception if all retries are exhausted.
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as exc:
            if attempt == max_retries - 1:
                raise exc
            sleep_time = (2 ** attempt) + random.uniform(0.0, 1.0)
            print(f"[RETRY] Attempt {attempt + 1} failed: {exc}. Retrying in {sleep_time:.1f}s...")
            time.sleep(sleep_time)


# ─── Analytics Tracker ────────────────────────────────────────────────────────

@dataclass
class AnalyticsTracker:
    """
    Tracks usage metrics across the conversation session.
    """
    query_count: int = 0
    escalation_count: int = 0
    persona_counts: dict = field(default_factory=lambda: defaultdict(int))
    retrieval_scores: list = field(default_factory=list)
    escalation_reasons: list = field(default_factory=list)

    def record_query(
        self,
        persona: str,
        retrieval_score: float,
        escalated: bool,
        escalation_reason: str = "",
    ) -> None:
        self.query_count += 1
        self.persona_counts[persona] += 1
        if retrieval_score > 0:
            self.retrieval_scores.append(retrieval_score)
        if escalated:
            self.escalation_count += 1
            self.escalation_reasons.append(escalation_reason)

    @property
    def avg_retrieval_score(self) -> float:
        if not self.retrieval_scores:
            return 0.0
        return sum(self.retrieval_scores) / len(self.retrieval_scores)

    @property
    def escalation_rate(self) -> float:
        if self.query_count == 0:
            return 0.0
        return self.escalation_count / self.query_count

    def summary(self) -> dict:
        return {
            "total_queries": self.query_count,
            "escalation_count": self.escalation_count,
            "escalation_rate_pct": round(self.escalation_rate * 100, 1),
            "avg_retrieval_confidence": round(self.avg_retrieval_score, 3),
            "persona_distribution": dict(self.persona_counts),
        }


# ─── Text Helpers ─────────────────────────────────────────────────────────────

def truncate(text: str, max_chars: int = 200) -> str:
    """Truncate text with an ellipsis if it exceeds max_chars."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."


def format_sources(chunks: list[dict]) -> list[str]:
    """Extract unique source names from retrieved chunks."""
    seen = set()
    sources = []
    for chunk in chunks:
        src = chunk.get("source", "Unknown")
        if src not in seen:
            sources.append(src)
            seen.add(src)
    return sources


def score_color(score: float) -> str:
    """Return a CSS color name based on retrieval confidence score."""
    if score >= 0.70:
        return "green"
    elif score >= 0.50:
        return "orange"
    else:
        return "red"


def persona_emoji(persona: str) -> str:
    """Return an emoji for each persona."""
    mapping = {
        "Technical Expert": "🔧",
        "Frustrated User": "😤",
        "Business Executive": "💼",
    }
    return mapping.get(persona, "👤")
