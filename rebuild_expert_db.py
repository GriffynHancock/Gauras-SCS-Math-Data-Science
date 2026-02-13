import json
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path

def ingest():
    chunks_file = Path("data/processed/refined_granular_chunks.json")
    if not chunks_file.exists():
        print(f"❌ Could not find {chunks_file}")
        return

    print(f"📖 Loading refined granular chunks...")
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    client = chromadb.PersistentClient(path="chroma_db")
    emb_fn = embedding_functions.DefaultEmbeddingFunction()

    # Recreate the advanced collection
    try:
        client.delete_collection("scsmath_advanced")
    except:
        pass
        
    collection = client.create_collection(
        name="scsmath_advanced",
        embedding_function=emb_fn
    )

    batch_size = 500
    print(f"📥 Ingesting {len(chunks)} chunks...")

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        ids = [c["id"] for c in batch]
        texts = [c["text"] for c in batch]
        metadatas = [c["metadata"] for c in batch]
        
        # Ensure all metadata values are primitive types for Chroma
        for m in metadatas:
            for k, v in m.items():
                if isinstance(v, list):
                    m[k] = ",".join(v)

        collection.add(ids=ids, documents=texts, metadatas=metadatas)
        if (i + len(batch)) % 2500 == 0 or (i + len(batch)) == len(chunks):
            print(f"  ✅ Ingested {i + len(batch)} / {len(chunks)}")

    print("🎉 Expert Rebuild complete!")

if __name__ == "__main__":
    ingest()
