"""
RAG setup script — run once before starting the app.
Loads all 4 compliance documents into ChromaDB using local embeddings.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
from chromadb.utils import embedding_functions

DOCS_DIR = os.path.join(os.path.dirname(__file__), "documents")
CHROMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")

DOCUMENT_METADATA = {
    "aml_typologies.txt": {"domain": "AML", "source": "aml_typologies.txt"},
    "kyc_policy.txt": {"domain": "KYC", "source": "kyc_policy.txt"},
    "aml_6th_directive.txt": {"domain": "AML", "source": "aml_6th_directive.txt"},
    "eu_ai_act.txt": {"domain": "COMPLIANCE", "source": "eu_ai_act.txt"},
}


def setup_rag():
    print("Initializing ChromaDB RAG system...")

    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    client = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        client.delete_collection("sentinel_docs")
        print("Existing collection deleted, recreating...")
    except Exception:
        pass

    collection = client.create_collection(
        name="sentinel_docs",
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )

    all_chunks = []
    all_ids = []
    all_metadatas = []
    chunk_counter = 0

    for filename, meta in DOCUMENT_METADATA.items():
        filepath = os.path.join(DOCS_DIR, filename)
        if not os.path.exists(filepath):
            print(f"WARNING: {filepath} not found, skipping.")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        chunks = [c.strip() for c in content.split("\n\n") if c.strip()]

        for chunk in chunks:
            chunk_id = f"chunk_{chunk_counter:04d}"
            all_chunks.append(chunk)
            all_ids.append(chunk_id)
            all_metadatas.append(meta.copy())
            chunk_counter += 1

        print(f"  Loaded {filename}: {len(chunks)} chunks")

    collection.add(
        documents=all_chunks,
        ids=all_ids,
        metadatas=all_metadatas,
    )

    print(f"\nRAG setup complete. {chunk_counter} total chunks loaded into ChromaDB.")
    print(f"Database stored at: {CHROMA_PATH}")
    return chunk_counter


if __name__ == "__main__":
    setup_rag()
