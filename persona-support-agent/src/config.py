"""
Configuration module — all thresholds, model names, and settings.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ─── API ───────────────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

# ─── Models ────────────────────────────────────────────────────────────────────
LLM_MODEL: str = "gemini-2.5-flash"
EMBEDDING_MODEL: str = "gemini-embedding-001"

# ─── RAG / Chunking ────────────────────────────────────────────────────────────
CHUNK_SIZE: int = 500
CHUNK_OVERLAP: int = 80
TOP_K: int = 3

# ─── Vector DB ─────────────────────────────────────────────────────────────────
CHROMA_DB_DIR: str = "./chroma_db"
COLLECTION_NAME: str = "support_kb"

# ─── Data directory ────────────────────────────────────────────────────────────
DATA_DIR: str = "./data"

# ─── Escalation thresholds ─────────────────────────────────────────────────────
# Escalate when best retrieval score < this value
ESCALATION_SCORE_THRESHOLD: float = 0.45

# Escalate when user has expressed dissatisfaction this many times
ESCALATION_DISSATISFACTION_COUNT: int = 2

# Keywords that always trigger escalation
ESCALATION_KEYWORDS: list[str] = [
    "refund",
    "billing dispute",
    "legal",
    "lawsuit",
    "delete account",
    "delete my account",
    "account deletion",
    "security breach",
    "data breach",
    "unauthorized access",
    "fraud",
    "charge back",
    "chargeback",
]

# ─── Dissatisfaction signal words ─────────────────────────────────────────────
DISSATISFACTION_SIGNALS: list[str] = [
    "still not working",
    "doesn't work",
    "doesn't help",
    "useless",
    "terrible",
    "awful",
    "worst",
    "unacceptable",
    "ridiculous",
    "pathetic",
    "i'm done",
    "i give up",
    "this is a joke",
    "no help",
    "waste of time",
    "not resolved",
    "still broken",
    "same issue",
    "same problem",
    "not fixed",
    "disappointed",
]

# ─── Memory ────────────────────────────────────────────────────────────────────
MEMORY_WINDOW: int = 5  # number of conversation turns to retain
