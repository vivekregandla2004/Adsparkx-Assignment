"""
RAG Pipeline — document ingestion, embedding, vector storage, and retrieval
using LangChain chunking, Gemini embeddings, and a pure-numpy in-memory
vector store (no compiled C/Rust extensions required).
"""
import os
import json
import uuid
import numpy as np
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google import genai

from src.config import (
    GEMINI_API_KEY,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K,
)
from src.utils import call_with_backoff

# Where to persist the index between sessions
_INDEX_DIR = Path("./vector_index")


class RAGPipeline:
    """
    Retrieval-Augmented Generation pipeline.

    Responsibilities:
    - Chunk documents with overlap
    - Generate Gemini embeddings (gemini-embedding-001)
    - Store vectors in-memory as numpy arrays (pure Python, no Rust/C++)
    - Persist index to disk as .npy + .json files for reuse across sessions
    - Retrieve top-k relevant chunks with cosine similarity scores
    """

    def __init__(self, index_dir: str = str(_INDEX_DIR)):
        self.genai_client = genai.Client(api_key=GEMINI_API_KEY)
        self.index_dir = Path(index_dir)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        # In-memory store
        self._embeddings: np.ndarray | None = None  # shape: (N, D)
        self._chunks: list[dict] = []               # [{text, source, page, section}]

        # Try to load persisted index
        self._load_index()

    # ─── Embedding ───────────────────────────────────────────────────────────

    def _get_embedding(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
        """Call Gemini embedding API with exponential backoff."""
        from google.genai import types as genai_types

        def _call():
            response = self.genai_client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text,
                config=genai_types.EmbedContentConfig(task_type=task_type),
            )
            return response.embeddings[0].values

        return call_with_backoff(_call)

    # ─── Persistence ─────────────────────────────────────────────────────────

    def _save_index(self):
        """Persist embeddings and metadata to disk."""
        self.index_dir.mkdir(parents=True, exist_ok=True)
        if self._embeddings is not None and len(self._chunks) > 0:
            np.save(self.index_dir / "embeddings.npy", self._embeddings)
            with open(self.index_dir / "chunks.json", "w", encoding="utf-8") as f:
                json.dump(self._chunks, f, ensure_ascii=False)

    def _load_index(self):
        """Load persisted embeddings and metadata from disk if available."""
        emb_path = self.index_dir / "embeddings.npy"
        meta_path = self.index_dir / "chunks.json"
        if emb_path.exists() and meta_path.exists():
            try:
                self._embeddings = np.load(str(emb_path))
                with open(meta_path, "r", encoding="utf-8") as f:
                    self._chunks = json.load(f)
                print(f"[RAG] Loaded persisted index: {len(self._chunks)} chunks.")
            except Exception as e:
                print(f"[RAG] Failed to load persisted index: {e}")
                self._embeddings = None
                self._chunks = []

    def _clear_index(self):
        """Clear in-memory index and delete persisted files."""
        self._embeddings = None
        self._chunks = []
        emb_path = self.index_dir / "embeddings.npy"
        meta_path = self.index_dir / "chunks.json"
        for p in (emb_path, meta_path):
            if p.exists():
                p.unlink()

    # ─── Cosine Similarity ───────────────────────────────────────────────────

    @staticmethod
    def _cosine_similarity(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
        """
        Compute cosine similarity between a query vector and a matrix of vectors.

        Args:
            query_vec: shape (D,)
            matrix:    shape (N, D)

        Returns:
            similarities: shape (N,) in range [-1, 1], higher = more similar
        """
        query_norm = np.linalg.norm(query_vec)
        matrix_norms = np.linalg.norm(matrix, axis=1)

        # Avoid division by zero
        query_norm = query_norm if query_norm > 0 else 1e-10
        matrix_norms = np.where(matrix_norms > 0, matrix_norms, 1e-10)

        dot_products = matrix @ query_vec
        return dot_products / (matrix_norms * query_norm)

    # ─── Indexing ────────────────────────────────────────────────────────────

    def build_index(self, documents: list[dict]) -> int:
        """
        Chunk, embed, and store all documents in memory (and persist to disk).

        Args:
            documents: List of {content: str, metadata: dict} from loaders.

        Returns:
            Total number of chunks stored.
        """
        self._clear_index()

        all_embeddings = []
        all_chunks = []

        for doc in documents:
            content = doc.get("content", "").strip()
            metadata = doc.get("metadata", {})
            source = metadata.get("source", "unknown")

            if not content:
                continue

            chunks = self.splitter.split_text(content)

            for idx, chunk in enumerate(chunks):
                chunk = chunk.strip()
                if not chunk:
                    continue

                embedding = self._get_embedding(chunk)
                all_embeddings.append(embedding)
                all_chunks.append(
                    {
                        "text": chunk,
                        "source": source,
                        "page": metadata.get("page", "1"),
                        "section": metadata.get("section", ""),
                        "chunk_index": idx,
                    }
                )

        if all_embeddings:
            self._embeddings = np.array(all_embeddings, dtype=np.float32)
            self._chunks = all_chunks
            self._save_index()

        total = len(all_chunks)
        print(f"[RAG] Index built: {total} chunks from {len(documents)} documents.")
        return total

    # ─── Retrieval ───────────────────────────────────────────────────────────

    def retrieve(self, query: str, top_k: int = TOP_K) -> list[dict]:
        """
        Retrieve the most relevant document chunks for a query.

        Args:
            query: The user's question.
            top_k: Number of chunks to retrieve.

        Returns:
            List of dicts: [{text, source, score, page, section}, ...]
            Score is cosine similarity in [0, 1] (higher = more relevant).
        """
        if self._embeddings is None or len(self._chunks) == 0:
            return []

        query_embedding = self._get_embedding(query, task_type="RETRIEVAL_QUERY")
        query_vec = np.array(query_embedding, dtype=np.float32)

        similarities = self._cosine_similarity(query_vec, self._embeddings)

        # Clamp to [0, 1] (cosine similarity can be slightly negative for unrelated docs)
        similarities = np.clip(similarities, 0.0, 1.0)

        k = min(top_k, len(self._chunks))
        top_indices = np.argsort(similarities)[::-1][:k]

        retrieved = []
        for i in top_indices:
            chunk = self._chunks[i]
            score = float(similarities[i])
            retrieved.append(
                {
                    "text": chunk["text"],
                    "source": chunk["source"],
                    "score": round(score, 4),
                    "page": chunk.get("page", "1"),
                    "section": chunk.get("section", ""),
                }
            )

        retrieved.sort(key=lambda x: x["score"], reverse=True)
        return retrieved

    def is_indexed(self) -> bool:
        """Return True if the index has any documents."""
        return self._embeddings is not None and len(self._chunks) > 0

    def chunk_count(self) -> int:
        """Return the total number of chunks in the index."""
        return len(self._chunks)
