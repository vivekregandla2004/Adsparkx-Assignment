# Persona-Aware Customer Support Agent

> An intelligent, production-ready AI customer support system that detects customer persona, retrieves grounded information from a knowledge base using RAG, generates persona-adaptive responses, and escalates unresolved cases to human support.

---

## Architecture Diagram

```
                        ┌─────────────────────────────┐
                        │         User Message          │
                        └─────────────┬───────────────┘
                                      │
                        ┌─────────────▼───────────────┐
                        │      Multi-Turn Memory        │
                        │   (last 5 conversation turns) │
                        └─────────────┬───────────────┘
                                      │
                        ┌─────────────▼───────────────┐
                        │      Persona Classifier       │
                        │   Gemini Structured Output    │
                        │  → Technical Expert           │
                        │  → Frustrated User            │
                        │  → Business Executive         │
                        └─────────────┬───────────────┘
                                      │
                        ┌─────────────▼───────────────┐
                        │        RAG Retrieval          │
                        │  ChromaDB + Gemini Embeddings │
                        │  gemini-embedding-001         │
                        │  → Top-3 Relevant Chunks      │
                        └─────────────┬───────────────┘
                                      │
                        ┌─────────────▼───────────────┐
                        │      Escalation Check         │
                        ├─────────────────────────────┤
                        │  Score < 0.45? ──────────────┼──► ESCALATE
                        │  Sensitive Keywords? ─────────┼──► ESCALATE
                        │  Dissatisfaction ≥ 2? ────────┼──► ESCALATE
                        │  No Documents? ───────────────┼──► ESCALATE
                        └─────────────┬───────────────┘
                                      │ (no escalation)
                        ┌─────────────▼───────────────┐
                        │   Adaptive Response Generator │
                        │   Gemini 2.5 Flash            │
                        │   Persona-specific prompts    │
                        │   Grounded in retrieved docs  │
                        └─────────────┬───────────────┘
                                      │
                  ┌───────────────────▼──────────────────────┐
                  │                Streamlit UI                │
                  │  Chat · Persona Badge · Confidence Bars   │
                  │  Source Citations · Handoff JSON · Charts │
                  └──────────────────────────────────────────┘
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Language** | Python 3.11+ |
| **UI** | Streamlit ≥1.35 |
| **LLM** | Google Gemini 2.5 Flash (`gemini-2.5-flash`) |
| **Embeddings** | Gemini `gemini-embedding-001` |
| **Vector DB** | ChromaDB (persistent) |
| **Chunking** | LangChain `RecursiveCharacterTextSplitter` |
| **PDF Parsing** | pypdf |
| **Config** | python-dotenv |

---

## Project Structure

```
persona-support-agent/
│
├── data/                          # Knowledge base documents
│   ├── password_reset_guide.pdf   # Required PDF document
│   ├── billing_policy.txt
│   ├── api_authentication.md
│   ├── login_troubleshooting.md
│   ├── account_lock_policy.txt
│   ├── cloud_access_guide.md
│   ├── refund_policy.md
│   ├── service_status.md
│   ├── integration_faq.txt
│   └── escalation_policy.md
│
├── src/
│   ├── __init__.py
│   ├── config.py             # All thresholds and settings
│   ├── classifier.py         # Gemini-based persona detection
│   ├── loaders.py            # TXT/MD/PDF document loaders
│   ├── rag_pipeline.py       # ChromaDB + embedding + retrieval
│   ├── response_generator.py # Persona-adaptive Gemini responses
│   ├── escalation.py         # Escalation logic + handoff JSON
│   ├── memory.py             # Sliding window conversation memory
│   ├── prompts.py            # All system prompt templates
│   └── utils.py              # Backoff, analytics, helpers
│
├── app.py                    # Main Streamlit application
├── create_pdf.py             # PDF generator (run once)
├── requirements.txt
├── .env.example
└── chroma_db/                # Auto-created by ChromaDB
```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/your-username/persona-support-agent.git
cd persona-support-agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:

```
GEMINI_API_KEY=your_actual_api_key_here
```

Get your API key at: https://aistudio.google.com/app/apikey

### 5. Generate the PDF knowledge base document (first time only)

```bash
python create_pdf.py
```

This creates `data/password_reset_guide.pdf`.

### 6. Run the application

```bash
streamlit run app.py
```

The app will automatically build the knowledge index on first launch.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API key from Google AI Studio |

---

## Features

### Persona Detection
- Uses Gemini structured JSON output for reliable classification
- Detects: **Technical Expert**, **Frustrated User**, **Business Executive**
- Incorporates last 5 conversation turns for context-aware detection
- Returns confidence score (0.0 – 1.0) and reasoning

### Persona Detection Strategy
| Persona | Signals |
|---------|---------|
| Technical Expert | API/log/config terminology, error codes, debugging questions |
| Frustrated User | Emotional language, exclamation marks, repeated complaints |
| Business Executive | Business impact, timelines, ROI, concise expectations |

### RAG Pipeline
- **Chunking:** `RecursiveCharacterTextSplitter` with `chunk_size=500`, `chunk_overlap=80`
- **Embedding:** Gemini `gemini-embedding-001` (3072-dimensional vectors)
- **Storage:** ChromaDB persistent storage with cosine similarity space
- **Retrieval:** Top-3 chunks with cosine similarity scoring
- **Metadata:** source filename, page number, section name per chunk

### Adaptive Responses
Each persona gets a distinct system prompt:
- **Technical Expert:** Root cause analysis, diagnostic steps, code examples, exact error codes
- **Frustrated User:** Warm empathy opening, simple numbered steps, plain language, reassurance
- **Business Executive:** Business impact lead, timeline, concise bullets, no jargon

All responses are strictly grounded in retrieved knowledge base content. No hallucination.

### Escalation Logic
Escalates when **any** of the following conditions are met:
1. **Low retrieval confidence:** best chunk score < 0.45 (configurable via sidebar)
2. **Sensitive keywords detected:** `refund`, `billing dispute`, `legal`, `delete account`, `fraud`, `chargeback`, etc.
3. **Repeated dissatisfaction:** user has expressed frustration ≥ 2 times (configurable)
4. **No documents found:** knowledge base returns empty results

### Human Handoff JSON
On escalation, generates:
```json
{
  "persona": "Frustrated User",
  "issue": "User's summarized query",
  "escalation_reason": "Why this was escalated",
  "conversation_history": [...],
  "documents_used": ["billing_policy.txt"],
  "attempted_steps": ["Previous resolution attempts"],
  "recommendation": "AI-generated recommendation for human agent",
  "confidence_score": 0.32
}
```

---

## Example Queries

| # | Query | Expected Persona | Behavior |
|---|-------|-----------------|---------|
| 1 | "Explain why API auth returns 401 and show logs." | Technical Expert | Detailed diagnostic steps, header analysis |
| 2 | "I've tried everything and nothing works! So frustrating!" | Frustrated User | Empathy-first, simple numbered steps |
| 3 | "How does this service outage affect our operations?" | Business Executive | Impact summary, SLA, timeline |
| 4 | "I want a refund immediately for duplicate charges." | Frustrated User | **Escalates** (refund keyword + billing) |
| 5 | "What are the header requirements for bearer token auth?" | Technical Expert | Technical specifications from API docs |

---

## Known Limitations

1. **API Rate Limits:** Gemini API has rate limits; exponential backoff handles transient failures but large knowledge bases take time to index.
2. **PDF Text Extraction:** Complex PDFs with tables, images, or non-standard fonts may have imperfect text extraction.
3. **Persona Accuracy:** Classification is based on single-message analysis; ambiguous messages may be misclassified.
4. **Session State:** Analytics and memory are session-scoped (lost on page refresh).
5. **No Authentication:** The UI has no login/auth — suitable for internal demos only.
6. **Context Window:** Very long conversations may exceed the LLM's effective context for response generation.

## Future Improvements

1. **LangGraph Workflow:** Convert to a stateful agentic graph for more sophisticated multi-step reasoning.
2. **Sentiment Analysis:** Real-time sentiment tracking for proactive dissatisfaction detection.
3. **Feedback Loop:** Thumbs up/down per response to collect preference data for fine-tuning.
4. **Database Persistence:** Store conversation history in PostgreSQL or SQLite for cross-session analytics.
5. **Human-in-the-Loop Dashboard:** A separate agent dashboard where human operators receive and respond to handoffs.
6. **Multi-language Support:** Detect and respond in the user's language.
7. **Voice Interface:** Add speech-to-text and text-to-speech for phone support simulation.
8. **Hybrid Search:** Combine BM25 keyword search with semantic similarity for better retrieval.
