"""
app.py — Main Streamlit UI for the Persona-Aware Customer Support Agent.

Run with:
    streamlit run app.py
"""
import json
import os
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ─── Page config (must be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title="Persona-Aware Support Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Imports (after page config) ─────────────────────────────────────────────
from src.config import DATA_DIR, ESCALATION_SCORE_THRESHOLD, ESCALATION_DISSATISFACTION_COUNT, TOP_K
from src.classifier import classify_persona
from src.loaders import load_documents
from src.rag_pipeline import RAGPipeline
from src.response_generator import generate_response
from src.escalation import check_escalation, detect_dissatisfaction, generate_handoff
from src.memory import ConversationMemory
from src.utils import AnalyticsTracker, persona_emoji, score_color, truncate

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* App background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        min-height: 100vh;
    }

    /* Main content */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1100px;
    }

    /* Header */
    .header-container {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    .header-title {
        font-size: 2rem;
        font-weight: 700;
        color: white;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .header-subtitle {
        color: rgba(255,255,255,0.85);
        font-size: 0.95rem;
        margin-top: 6px;
    }

    /* Chat messages */
    .chat-message {
        border-radius: 16px;
        padding: 16px 20px;
        margin: 10px 0;
        animation: fadeIn 0.3s ease-in;
        position: relative;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .user-message {
        background: linear-gradient(135deg, #667eea22, #764ba222);
        border: 1px solid #667eea55;
        border-left: 4px solid #667eea;
        margin-left: 60px;
    }
    .assistant-message {
        background: linear-gradient(135deg, #11998e11, #38ef7d11);
        border: 1px solid #38ef7d33;
        border-left: 4px solid #38ef7d;
        margin-right: 60px;
    }
    .escalation-message {
        background: linear-gradient(135deg, #f8535311, #ff6b6b11);
        border: 1px solid #f8535355;
        border-left: 4px solid #f85353;
        margin-right: 60px;
    }
    .message-role {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 6px;
        opacity: 0.7;
        color: white;
    }
    .message-content {
        color: rgba(255, 255, 255, 0.92);
        font-size: 0.95rem;
        line-height: 1.6;
    }

    /* Persona badge */
    .persona-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        margin: 8px 0;
    }
    .badge-technical { background: rgba(99, 179, 237, 0.2); color: #63b3ed; border: 1px solid #63b3ed55; }
    .badge-frustrated { background: rgba(252, 129, 74, 0.2); color: #fc814a; border: 1px solid #fc814a55; }
    .badge-executive { background: rgba(154, 230, 180, 0.2); color: #9ae6b4; border: 1px solid #9ae6b455; }
    .badge-escalated { background: rgba(248, 83, 83, 0.2); color: #f85353; border: 1px solid #f8535355; }

    /* Confidence bar */
    .confidence-bar-container {
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        height: 8px;
        width: 100%;
        margin: 4px 0;
        overflow: hidden;
    }
    .confidence-bar-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 0.5s ease;
    }

    /* Source chip */
    .source-chip {
        display: inline-block;
        background: rgba(102, 126, 234, 0.2);
        border: 1px solid rgba(102, 126, 234, 0.4);
        color: #a78bfa;
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 0.75rem;
        font-family: 'Courier New', monospace;
        margin: 2px 3px;
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 14px;
        padding: 16px;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #a78bfa;
    }
    .metric-label {
        font-size: 0.75rem;
        color: rgba(255,255,255,0.6);
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }

    /* Chat Input */
    .stTextInput input {
        background: rgba(255,255,255,0.08) !important;
        color: white !important;
        border: 1.5px solid rgba(255,255,255,0.15) !important;
        border-radius: 18px !important;
        padding: 14px 18px !important;
        font-size: 16px !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
    }

    /* Focus Effect */
    .stTextInput input:focus {
        border: 2px solid #7C5CFF !important;
        box-shadow: 0 0 18px rgba(124,92,255,0.5) !important;
        background: rgba(255,255,255,0.12) !important;
        outline: none !important;
    }

    /* Placeholder */
    .stTextInput input::placeholder {
        color: rgba(255,255,255,0.55) !important;
    }

    /* Textarea (file uploader notes, etc.) */
    .stTextArea > div > div > textarea {
        background: rgba(255,255,255,0.07) !important;
        border: 1.5px solid rgba(255,255,255,0.15) !important;
        border-radius: 12px !important;
        color: white !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
    }
    .stTextArea > div > div > textarea:focus {
        border-color: #7C5CFF !important;
        box-shadow: 0 0 18px rgba(124,92,255,0.5) !important;
    }

    /* Send Button */
    .stButton > button {
        background: linear-gradient(90deg, #6C63FF, #9B59FF) !important;
        color: white !important;
        border-radius: 18px !important;
        height: 52px !important;
        border: none !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 25px rgba(124,92,255,0.4) !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.07);
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.05) !important;
        border-radius: 10px !important;
        color: rgba(255,255,255,0.8) !important;
    }

    /* Handoff JSON */
    .handoff-container {
        background: rgba(248, 83, 83, 0.08);
        border: 1px solid rgba(248, 83, 83, 0.3);
        border-radius: 12px;
        padding: 16px;
        margin-top: 12px;
    }

    /* Section labels */
    .section-label {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: rgba(255,255,255,0.45);
        margin-bottom: 4px;
    }

    /* Index status */
    .index-status {
        background: rgba(56, 239, 125, 0.1);
        border: 1px solid rgba(56, 239, 125, 0.3);
        border-radius: 10px;
        padding: 10px 14px;
        font-size: 0.85rem;
        color: #38ef7d;
    }
    .index-status-empty {
        background: rgba(252, 129, 74, 0.1);
        border: 1px solid rgba(252, 129, 74, 0.3);
        border-radius: 10px;
        padding: 10px 14px;
        font-size: 0.85rem;
        color: #fc814a;
    }

    /* Divider */
    hr { border-color: rgba(255,255,255,0.08) !important; }

    /* Selectbox, slider */
    .stSelectbox > div, .stSlider { color: white !important; }

    /* Toast / success */
    .stSuccess { background: rgba(56,239,125,0.15) !important; border-radius: 10px !important; }
    .stWarning { background: rgba(252,129,74,0.15) !important; border-radius: 10px !important; }
    .stError   { background: rgba(248,83,83,0.15) !important;  border-radius: 10px !important; }

    /* Tab */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        color: rgba(255,255,255,0.6) !important;
        border-radius: 8px !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ─── Session State Initialisation ─────────────────────────────────────────────

def init_session_state():
    defaults = {
        "messages": [],            # {role, content, metadata}
        "memory": ConversationMemory(),
        "rag": None,               # RAGPipeline instance
        "analytics": AnalyticsTracker(),
        "dissatisfaction_count": 0,
        "attempted_steps": [],
        "index_built": False,
        "chunk_count": 0,
        "last_persona": None,
        "last_chunks": [],
        "last_escalation": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# ─── RAG Initialisation ──────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def get_rag_pipeline():
    return RAGPipeline()


def build_knowledge_index(uploaded_files=None, show_progress=True):
    """Load docs (from data/ and optionally uploaded files) and build the index."""
    rag = get_rag_pipeline()

    # Load from data directory
    docs = load_documents(DATA_DIR)

    # Process uploaded files
    if uploaded_files:
        import tempfile
        for uf in uploaded_files:
            suffix = Path(uf.name).suffix.lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uf.read())
                tmp_path = tmp.name
            try:
                from src.loaders import _load_text_file, _load_pdf_file
                if suffix in {".txt", ".md"}:
                    new_docs = _load_text_file(Path(tmp_path))
                    for d in new_docs:
                        d["metadata"]["source"] = uf.name
                elif suffix == ".pdf":
                    new_docs = _load_pdf_file(Path(tmp_path))
                    for d in new_docs:
                        d["metadata"]["source"] = uf.name
                else:
                    new_docs = []
                docs.extend(new_docs)
            finally:
                os.unlink(tmp_path)

    if not docs:
        return 0

    progress_bar = st.progress(0, text="Building knowledge index...") if show_progress else None

    if progress_bar:
        progress_bar.progress(20, text="Chunking documents...")
    time.sleep(0.2)

    if progress_bar:
        progress_bar.progress(40, text="Generating embeddings (this may take a minute)...")

    chunk_count = rag.build_index(docs)

    if progress_bar:
        progress_bar.progress(100, text="Index ready!")
        time.sleep(0.5)
        progress_bar.empty()

    st.session_state["rag"] = rag
    st.session_state["index_built"] = True
    st.session_state["chunk_count"] = chunk_count
    return chunk_count


# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        """
        <div style='text-align:center; padding: 10px 0 20px 0;'>
            <div style='font-size:2.5rem;'>🤖</div>
            <div style='color:white; font-weight:700; font-size:1.1rem;'>Support Agent</div>
            <div style='color:rgba(255,255,255,0.5); font-size:0.78rem;'>Persona-Aware AI</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Index Status ──────────────────────────────────────────────────────────
    st.markdown("**📚 Knowledge Base**")

    rag = get_rag_pipeline()
    is_indexed = rag.is_indexed()

    if is_indexed or st.session_state["index_built"]:
        cnt = st.session_state.get("chunk_count") or rag.chunk_count()
        st.markdown(
            f'<div class="index-status">✅ Index ready · {cnt} chunks</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="index-status-empty">⚠️ Index not built yet</div>',
            unsafe_allow_html=True,
        )

    st.markdown("")

    # Upload docs
    uploaded_files = st.file_uploader(
        "Upload Documents",
        type=["txt", "md", "pdf"],
        accept_multiple_files=True,
        help="Upload additional support documents to extend the knowledge base.",
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔨 Build Index", use_container_width=True, key="build_btn"):
            with st.spinner("Building index..."):
                cnt = build_knowledge_index(uploaded_files=uploaded_files)
            if cnt > 0:
                st.success(f"✅ {cnt} chunks indexed!")
                st.rerun()
            else:
                st.error("No documents found. Add files to the `data/` folder.")
    with col2:
        if st.button("🔄 Rebuild", use_container_width=True, key="rebuild_btn"):
            # Clear chroma cache
            get_rag_pipeline.clear()
            st.session_state["index_built"] = False
            st.session_state["chunk_count"] = 0
            with st.spinner("Rebuilding..."):
                cnt = build_knowledge_index(uploaded_files=uploaded_files)
            if cnt > 0:
                st.success(f"✅ {cnt} chunks!")
                st.rerun()

    st.divider()

    # ── Escalation Settings ───────────────────────────────────────────────────
    st.markdown("**⚙️ Escalation Settings**")
    score_threshold = st.slider(
        "Score Threshold",
        min_value=0.1,
        max_value=0.9,
        value=ESCALATION_SCORE_THRESHOLD,
        step=0.05,
        help="Retrieval confidence below this triggers escalation.",
        key="score_threshold_slider",
    )
    dissatisfaction_threshold = st.slider(
        "Dissatisfaction Limit",
        min_value=1,
        max_value=5,
        value=ESCALATION_DISSATISFACTION_COUNT,
        step=1,
        help="Number of dissatisfied messages before escalation.",
        key="dissatisfaction_slider",
    )

    st.divider()

    # ── Chat Controls ──────────────────────────────────────────────────────────
    st.markdown("**💬 Chat Controls**")
    if st.button("🗑️ Reset Chat", use_container_width=True, key="reset_btn"):
        st.session_state["messages"] = []
        st.session_state["memory"] = ConversationMemory()
        st.session_state["dissatisfaction_count"] = 0
        st.session_state["attempted_steps"] = []
        st.session_state["last_persona"] = None
        st.session_state["last_chunks"] = []
        st.session_state["last_escalation"] = None
        st.rerun()

    st.divider()

    # ── Conversation History Preview ───────────────────────────────────────────
    st.markdown("**📜 Recent History**")
    memory: ConversationMemory = st.session_state["memory"]
    if memory.turn_count == 0:
        st.caption("No conversation yet.")
    else:
        for msg in memory.get_history()[-6:]:
            role_icon = "👤" if msg["role"] == "user" else "🤖"
            st.caption(f"{role_icon} {truncate(msg['content'], 60)}")

    st.divider()

    # ── Quick-test queries ────────────────────────────────────────────────────
    st.markdown("**🧪 Test Queries**")
    test_queries = {
        "🔧 Technical": "Explain why the API auth returns 401 and how to debug it with logs.",
        "😤 Frustrated": "I've tried everything and nothing works! This is so frustrating!",
        "💼 Executive": "How does this service outage affect our operations and when will it be resolved?",
        "🚨 Escalation": "I want a refund immediately for these duplicate charges.",
    }
    for label, query in test_queries.items():
        if st.button(label, use_container_width=True, key=f"test_{label}"):
            st.session_state["_inject_query"] = query
            st.rerun()


# ─── Main Content ─────────────────────────────────────────────────────────────

# Header
st.markdown(
    """
    <div class="header-container">
        <div class="header-title">🤖 Persona-Aware Customer Support Agent</div>
        <div class="header-subtitle">
            Powered by Google Gemini 2.5 Flash · RAG · ChromaDB · Multi-turn Memory
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Tabs
tab_chat, tab_analytics = st.tabs(["💬 Chat", "📊 Analytics"])


# ─── Analytics Tab ────────────────────────────────────────────────────────────

with tab_analytics:
    analytics: AnalyticsTracker = st.session_state["analytics"]
    summary = analytics.summary()

    st.markdown("### Session Analytics Dashboard")

    m1, m2, m3, m4 = st.columns(4)

    def metric_card(col, value, label, color="#a78bfa"):
        col.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value" style="color:{color};">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    metric_card(m1, summary["total_queries"], "Total Queries")
    metric_card(m2, summary["escalation_count"], "Escalations", "#f85353")
    metric_card(m3, f"{summary['avg_retrieval_confidence']:.2f}", "Avg Confidence", "#38ef7d")
    metric_card(m4, f"{summary['escalation_rate_pct']}%", "Escalation Rate", "#fc814a")

    st.divider()

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("**Persona Distribution**")
        persona_dist = summary["persona_distribution"]
        if persona_dist:
            for persona, count in persona_dist.items():
                pct = count / max(summary["total_queries"], 1)
                emoji = persona_emoji(persona)
                st.markdown(f"**{emoji} {persona}** — {count} ({pct:.0%})")
                st.progress(pct)
        else:
            st.caption("No data yet. Start chatting!")

    with col_r:
        st.markdown("**Retrieval Confidence History**")
        if analytics.retrieval_scores:
            import pandas as pd
            df = pd.DataFrame(
                {
                    "Query": list(range(1, len(analytics.retrieval_scores) + 1)),
                    "Confidence": analytics.retrieval_scores,
                }
            )
            st.line_chart(df.set_index("Query")["Confidence"], color="#667eea")
        else:
            st.caption("No retrieval data yet.")

    if analytics.escalation_reasons:
        st.divider()
        st.markdown("**Escalation Log**")
        for i, reason in enumerate(analytics.escalation_reasons, 1):
            st.markdown(f"🚨 **{i}.** {reason}")


# ─── Chat Tab ────────────────────────────────────────────────────────────────

with tab_chat:

    # Auto-build index if not done
    rag_instance = get_rag_pipeline()
    if not rag_instance.is_indexed() and not st.session_state["index_built"]:
        with st.spinner("🔨 Building knowledge index on first launch..."):
            cnt = build_knowledge_index()
        if cnt > 0:
            st.success(f"✅ Knowledge base indexed: {cnt} chunks ready.", icon="📚")
        else:
            st.warning(
                "⚠️ No documents found in `data/`. Add support documents and click **Build Index** in the sidebar.",
                icon="📁",
            )

    # ── Chat History Display ──────────────────────────────────────────────────
    chat_container = st.container()
    with chat_container:
        for msg_data in st.session_state["messages"]:
            role = msg_data["role"]
            content = msg_data["content"]
            metadata = msg_data.get("metadata", {})

            if role == "user":
                st.markdown(
                    f"""
                    <div class="chat-message user-message">
                        <div class="message-role">👤 You</div>
                        <div class="message-content">{content}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif role == "assistant":
                escalated = metadata.get("escalated", False)
                persona = metadata.get("persona", "")
                confidence = metadata.get("confidence", 0.0)
                sources = metadata.get("sources", [])
                retrieval_score = metadata.get("retrieval_score", 0.0)
                handoff = metadata.get("handoff", None)

                # Persona badge CSS class
                badge_class = {
                    "Technical Expert": "badge-technical",
                    "Frustrated User": "badge-frustrated",
                    "Business Executive": "badge-executive",
                }.get(persona, "badge-technical")

                msg_class = "escalation-message" if escalated else "assistant-message"

                st.markdown(
                    f"""
                    <div class="chat-message {msg_class}">
                        <div class="message-role">🤖 Support Agent</div>
                    """,
                    unsafe_allow_html=True,
                )

                # Persona + confidence
                if persona:
                    p_emoji = persona_emoji(persona)
                    conf_pct = int(confidence * 100)
                    conf_color = score_color(confidence)
                    st.markdown(
                        f"""
                        <div style="display:flex; align-items:center; gap:12px; margin-bottom:10px; flex-wrap:wrap;">
                            <span class="persona-badge {badge_class}">{p_emoji} {persona}</span>
                            <div style="flex:1; min-width:120px;">
                                <div class="section-label">Persona Confidence</div>
                                <div class="confidence-bar-container">
                                    <div class="confidence-bar-fill" style="width:{conf_pct}%; background:{conf_color};"></div>
                                </div>
                                <div style="font-size:0.72rem; color:rgba(255,255,255,0.5);">{conf_pct}%</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # Escalation badge
                if escalated:
                    st.markdown(
                        '<span class="persona-badge badge-escalated">🚨 ESCALATED TO HUMAN</span>',
                        unsafe_allow_html=True,
                    )

                # Message content
                st.markdown(
                    f'<div class="message-content">{content}</div>',
                    unsafe_allow_html=True,
                )

                # Sources
                if sources:
                    sources_html = "".join(
                        f'<span class="source-chip">📄 {s}</span>' for s in sources
                    )
                    st.markdown(
                        f'<div style="margin-top:10px;"><div class="section-label">Sources</div>{sources_html}</div>',
                        unsafe_allow_html=True,
                    )

                # Retrieval confidence bar
                if retrieval_score > 0:
                    rs_pct = int(retrieval_score * 100)
                    rs_color = score_color(retrieval_score)
                    st.markdown(
                        f"""
                        <div style="margin-top:8px;">
                            <div class="section-label">Retrieval Confidence</div>
                            <div class="confidence-bar-container">
                                <div class="confidence-bar-fill" style="width:{rs_pct}%; background:{rs_color};"></div>
                            </div>
                            <div style="font-size:0.72rem; color:rgba(255,255,255,0.5);">{rs_pct}%</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                st.markdown("</div>", unsafe_allow_html=True)

                # Retrieved chunks expander
                chunks = metadata.get("chunks", [])
                if chunks:
                    with st.expander("🔍 Retrieved Knowledge Chunks", expanded=False):
                        for i, chunk in enumerate(chunks, 1):
                            c_score = chunk.get("score", 0.0)
                            c_source = chunk.get("source", "?")
                            c_text = chunk.get("text", "")
                            c_page = chunk.get("page", "")
                            page_info = f" · Page {c_page}" if c_page and c_page != "1" else ""
                            score_pct = int(c_score * 100)
                            s_color = score_color(c_score)
                            st.markdown(
                                f"""
                                <div style="background:rgba(255,255,255,0.04); border-radius:10px;
                                            padding:12px; margin-bottom:10px; border:1px solid rgba(255,255,255,0.08);">
                                    <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                                        <span class="source-chip">📄 {c_source}{page_info}</span>
                                        <span style="font-size:0.75rem; color:{s_color};">Score: {score_pct}%</span>
                                    </div>
                                    <div style="font-size:0.85rem; color:rgba(255,255,255,0.75); line-height:1.5;">{c_text}</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                # Handoff JSON expander
                if handoff:
                    with st.expander("📋 Human Handoff Summary", expanded=True):
                        st.markdown(
                            '<div class="handoff-container">',
                            unsafe_allow_html=True,
                        )
                        st.json(handoff)
                        st.markdown("</div>", unsafe_allow_html=True)

                        # Download button
                        st.download_button(
                            label="⬇️ Download Handoff JSON",
                            data=json.dumps(handoff, indent=2),
                            file_name="handoff_summary.json",
                            mime="application/json",
                            key=f"dl_{id(handoff)}",
                        )

    # ── Input Area ────────────────────────────────────────────────────────────
    st.divider()

    # Handle injected query from sidebar test buttons
    injected_query = st.session_state.pop("_inject_query", None)

    with st.form(key="chat_form", clear_on_submit=True):
        col_input, col_btn = st.columns([5, 1])
        with col_input:
            user_input = st.text_input(
                "Your message",
                value=injected_query or "",
                placeholder="Type your support question here...",
                label_visibility="collapsed",
                key="user_input_field",
            )
        with col_btn:
            submitted = st.form_submit_button("Send ➤", use_container_width=True)

    # ── Processing ────────────────────────────────────────────────────────────
    if submitted and user_input.strip():
        query = user_input.strip()

        # Check API key
        if not os.getenv("GEMINI_API_KEY"):
            st.error("❌ GEMINI_API_KEY not set. Add it to your `.env` file and restart.", icon="🔑")
            st.stop()

        # Ensure index is built
        rag_inst = get_rag_pipeline()
        if not rag_inst.is_indexed():
            st.warning("⚠️ Knowledge base not indexed yet. Building now...", icon="⏳")
            cnt = build_knowledge_index()
            if cnt == 0:
                st.error("Failed to build index. Check that `data/` has documents.")
                st.stop()
            st.rerun()

        # Store user message
        st.session_state["messages"].append({"role": "user", "content": query, "metadata": {}})
        st.session_state["memory"].add("user", query)

        # Check dissatisfaction
        if detect_dissatisfaction(query):
            st.session_state["dissatisfaction_count"] += 1

        with st.spinner("🧠 Processing your query..."):
            try:
                # 1. Classify persona
                history = st.session_state["memory"].get_history()[:-1]  # exclude current
                persona_result = classify_persona(query, conversation_history=history)
                persona = persona_result["persona"]
                confidence = persona_result["confidence"]
                reasoning = persona_result["reasoning"]
                st.session_state["last_persona"] = persona

                # 2. Retrieve chunks
                chunks = rag_inst.retrieve(query, top_k=TOP_K)
                st.session_state["last_chunks"] = chunks
                best_score = max((c["score"] for c in chunks), default=0.0)

                # 3. Escalation check
                escalation_result = check_escalation(
                    chunks=chunks,
                    dissatisfaction_count=st.session_state["dissatisfaction_count"],
                    query=query,
                    custom_score_threshold=st.session_state.get(
                        "score_threshold_slider", ESCALATION_SCORE_THRESHOLD
                    ),
                    custom_dissatisfaction_threshold=st.session_state.get(
                        "dissatisfaction_slider", ESCALATION_DISSATISFACTION_COUNT
                    ),
                )
                should_escalate = escalation_result["should_escalate"]
                escalation_reason = escalation_result["reason"]

                # 4a. Escalate
                if should_escalate:
                    handoff = generate_handoff(
                        persona=persona,
                        query=query,
                        conversation_history=st.session_state["memory"].get_history(),
                        chunks=chunks,
                        attempted_steps=st.session_state["attempted_steps"],
                        escalation_reason=escalation_reason,
                    )
                    st.session_state["last_escalation"] = handoff

                    response_text = (
                        "I'm sorry, but I'm unable to fully resolve your request with the "
                        "information available to me. I've escalated your case to a human "
                        "support specialist who will reach out to you shortly. Please review "
                        "the handoff summary below for details."
                    )
                    sources_list = list({c.get("source") for c in chunks})
                    metadata = {
                        "persona": persona,
                        "confidence": confidence,
                        "escalated": True,
                        "escalation_reason": escalation_reason,
                        "sources": sources_list,
                        "retrieval_score": best_score,
                        "chunks": chunks,
                        "handoff": handoff,
                        "reasoning": reasoning,
                    }

                    # Analytics
                    st.session_state["analytics"].record_query(
                        persona=persona,
                        retrieval_score=best_score,
                        escalated=True,
                        escalation_reason=escalation_reason,
                    )

                # 4b. Generate adaptive response
                else:
                    gen_result = generate_response(
                        query=query,
                        persona=persona,
                        chunks=chunks,
                        conversation_history=history,
                    )
                    response_text = gen_result["response"]
                    sources_list = gen_result["sources"]

                    # Track as attempted step
                    st.session_state["attempted_steps"].append(
                        f"Provided {persona} response using {', '.join(sources_list) or 'no sources'}"
                    )

                    metadata = {
                        "persona": persona,
                        "confidence": confidence,
                        "escalated": False,
                        "sources": sources_list,
                        "retrieval_score": best_score,
                        "chunks": chunks,
                        "handoff": None,
                        "reasoning": reasoning,
                    }

                    # Analytics
                    st.session_state["analytics"].record_query(
                        persona=persona,
                        retrieval_score=best_score,
                        escalated=False,
                    )

                # Store assistant message
                st.session_state["messages"].append(
                    {"role": "assistant", "content": response_text, "metadata": metadata}
                )
                st.session_state["memory"].add("assistant", response_text)

            except Exception as exc:
                st.error(f"❌ An error occurred: {exc}", icon="⚠️")
                import traceback
                with st.expander("Error Details"):
                    st.code(traceback.format_exc())

        st.rerun()


# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style='text-align:center; padding:20px 0 10px 0; color:rgba(255,255,255,0.3); font-size:0.75rem;'>
        Persona-Aware Customer Support Agent · Powered by Google Gemini 2.5 Flash + ChromaDB
    </div>
    """,
    unsafe_allow_html=True,
)
