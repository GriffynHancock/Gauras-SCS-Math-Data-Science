import json
import torch
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions
import numpy as np
from tqdm import tqdm

def compute_embeddings():
    input_file = Path("data/processed/canonical_chunks.jsonl")
    db_path = "chroma_db"
    collection_name = "chunks_collection"

    if not input_file.exists():
        print(f"❌ Input file {input_file} not found.")
        return

    print(f"🚀 Loading embedding model (BGE-M3)...")
    # Using BGE-M3 for multilingual support as requested in NEXT PHASE.md
    model = SentenceTransformer('BAAI/bge-m3')

    client = chromadb.PersistentClient(path=db_path)
    
    # We'll use the model to generate embeddings manually and then add to Chroma
    # This gives us more control and matches the requirement to store them in chunk records.
    
    try:
        client.delete_collection(collection_name)
    except:
        pass
    
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    print(f"📖 Reading canonical chunks...")
    chunks = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            chunks.append(json.loads(line))

    texts = [c["chunk_text"] for c in chunks]
    ids = [c["chunk_id"] for c in chunks]
    metadatas = []
    for c in chunks:
        # Flatten metadata for Chroma (Chroma doesn't like nested dicts)
        meta = {
            "doc_id": c["doc_id"],
            "language": c["language"],
            "chunk_type": c["chunk_type"],
            "book": c["structural_path"].get("book") or "",
            "chapter": str(c["structural_path"].get("chapter") or ""),
            "verse": str(c["structural_path"].get("verse") or "")
        }
        # Add original metadata fields if they are simple types
        for k, v in c["metadata"].items():
            if isinstance(v, (str, int, float, bool)) and k not in meta:
                meta[k] = v
        metadatas.append(meta)

    batch_size = 32
    print(f"🧠 Computing embeddings and ingesting to ChromaDB ({len(texts)} chunks)...")
    
    for i in tqdm(range(0, len(texts), batch_size)):
        batch_texts = texts[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        batch_metadatas = metadatas[i:i+batch_size]
        
        # Compute embeddings
        batch_embeddings = model.encode(batch_texts, normalize_embeddings=True)
        
        # Add to ChromaDB
        collection.add(
            ids=batch_ids,
            embeddings=batch_embeddings.tolist(),
            documents=batch_texts,
            metadatas=batch_metadatas
        )

    print(f"✅ Embeddings computed and persisted to collection '{collection_name}' in {db_path}")

if __name__ == "__main__":
    compute_embeddings()
