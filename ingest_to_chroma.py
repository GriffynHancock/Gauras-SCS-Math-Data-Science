import json
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path

def ingest():
    # 1. Load enriched chunks
    chunks_file = Path("data/processed/enriched_chunks.json")
    if not chunks_file.exists():
        print(f"❌ Could not find {chunks_file}")
        return

    print(f"📖 Loading chunks from {chunks_file}...")
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    # 2. Setup ChromaDB
    print("🚀 Initializing ChromaDB...")
    client = chromadb.PersistentClient(path="chroma_db")
    
    # Use a high-quality local embedding function
    # 'all-MiniLM-L6-v2' is standard, but we can use something more 'accurate' if needed.
    # By default, Chroma uses all-MiniLM-L6-v2.
    emb_fn = embedding_functions.DefaultEmbeddingFunction()

    collection = client.get_or_create_collection(
        name="scsmath_rag",
        embedding_function=emb_fn
    )

    # 3. Ingest in batches
    batch_size = 500
    print(f"📥 Ingesting {len(chunks)} chunks in batches of {batch_size}...")

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        
        ids = [c["id"] for c in batch]
        texts = [c["text"] for c in batch]
        metadatas = [c["metadata"] for c in batch]
        
        collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )
        print(f"  ✅ Ingested {i + len(batch)} / {len(chunks)}")

    print("🎉 Ingestion complete!")

if __name__ == "__main__":
    ingest()
