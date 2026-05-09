"""
RAG retriever — singleton ChromaDB client for efficient querying.
"""
import os
import chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")

_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is not None:
        return _collection

    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    _client = chromadb.PersistentClient(path=CHROMA_PATH)
    _collection = _client.get_collection(
        name="sentinel_docs",
        embedding_function=embedding_fn,
    )
    return _collection


def retrieve(query: str, domain: str = None, n_results: int = 2) -> str:
    """
    Query ChromaDB for relevant compliance documents.
    domain: "AML", "KYC", "COMPLIANCE", or None for all.
    Returns formatted string with source and chunk text.
    """
    try:
        collection = _get_collection()

        where_filter = None
        if domain:
            where_filter = {"domain": {"$eq": domain}}

        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter,
        )

        if not results["documents"] or not results["documents"][0]:
            return "No relevant regulations retrieved."

        formatted = ""
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            source = meta.get("source", "unknown")
            formatted += f"[Source: {source}]\n{doc}\n\n"

        return formatted.strip()

    except Exception as e:
        return f"RAG retrieval error: {str(e)}"
