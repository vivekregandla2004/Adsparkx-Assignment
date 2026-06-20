"""
RAG Pipeline — document ingestion, embedding, vector storage, and retrieval
using LangChain chunking, Gemini embeddings, and ChromaDB.
"""
import os
import uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google import genai
import chromadb

from src.config import (
    GEMINI_API_KEY,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    CHROMA_DB_DIR,
    COLLECTION_NAME,
    TOP_K,
)
from src.utils import call_with_backoff


class RAGPipeline:
    """
    Retrieval-Augmented Generation pipeline.

    Responsibilities:
    - Chunk documents with overlap
    - Generate Gemini embeddings (text-embedding-004)
    - Persist to ChromaDB
    - Retrieve top-k relevant chunks with confidence scores
    """

    def __init__(self, db_dir: str = CHROMA_DB_DIR):
        self.genai_client = genai.Client(api_key=GEMINI_API_KEY)
        self.chroma_client = chromadb.PersistentClient(path=db_dir)
        self.collection = self.chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    # ─── Embedding ───────────────────────────────────────────────────────────

    def _get_embedding(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
        """Call Gemini embedding API with backoff."""
        from google.genai import types as genai_types

        def _call():
            response = self.genai_client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=text,
                config=genai_types.EmbedContentConfig(
                    task_type=task_type,
                ),
            )
            return response.embeddings[0].values

        return call_with_backoff(_call)

    # ─── Indexing ────────────────────────────────────────────────────────────

    def build_index(self, documents: list[dict]) -> int:
        """
        Chunk, embed, and store all documents in ChromaDB.

        Args:
            documents: List of {content: str, metadata: dict} from loaders.

        Returns:
            Total number of chunks stored.
        """
        # Clear existing collection
        self.chroma_client.delete_collection(COLLECTION_NAME)
        self.collection = self.chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        total_chunks = 0
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
                chunk_id = f"{source}_chunk_{idx}_{uuid.uuid4().hex[:8]}"

                self.collection.add(
                    ids=[chunk_id],
                    embeddings=[embedding],
                    metadatas=[
                        {
                            "source": source,
                            "page": metadata.get("page", "1"),
                            "section": metadata.get("section", ""),
                            "chunk_index": idx,
                        }
                    ],
                    documents=[chunk],
                )
                total_chunks += 1

        print(f"[RAG] Index built: {total_chunks} chunks from {len(documents)} documents.")
        return total_chunks

    # ─── Retrieval ───────────────────────────────────────────────────────────

    def retrieve(self, query: str, top_k: int = TOP_K) -> list[dict]:
        """
        Retrieve the most relevant document chunks for a query.

        Args:
            query: The user's question.
            top_k: Number of chunks to retrieve.

        Returns:
            List of dicts: [{text, source, score, page, section}, ...]
            Score is a cosine similarity value in [0, 1] (higher = more relevant).
        """
        if self.collection.count() == 0:
            return []

        query_embedding = self._get_embedding(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        retrieved: list[dict] = []
        if not results or not results.get("documents"):
            return retrieved

        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0]

        for i in range(len(docs)):
            # ChromaDB cosine distance ∈ [0, 2]; convert to similarity ∈ [0, 1]
            distance = float(distances[i]) if distances else 1.0
            score = max(0.0, min(1.0, 1.0 - (distance / 2.0)))

            retrieved.append(
                {
                    "text": docs[i],
                    "source": metas[i].get("source", "unknown"),
                    "score": round(score, 4),
                    "page": metas[i].get("page", "1"),
                    "section": metas[i].get("section", ""),
                }
            )

        # Sort by score descending
        retrieved.sort(key=lambda x: x["score"], reverse=True)
        return retrieved

    def is_indexed(self) -> bool:
        """Return True if the collection has any documents."""
        return self.collection.count() > 0

    def chunk_count(self) -> int:
        """Return the total number of chunks in the collection."""
        return self.collection.count()
