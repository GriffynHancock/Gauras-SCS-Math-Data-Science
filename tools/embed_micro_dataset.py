import json
import torch
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb
from tqdm import tqdm

def embed_micro_dataset():
    input_file = Path("data/micro_test/processed/enriched_chunks.jsonl")
    db_path = "chroma_db"
    collection_name = "micro_chunks_collection"

    if not input_file.exists():
        print(f"❌ Input file {input_file} not found.")
        return

    print(f"🚀 Loading embedding model (BGE-M3) on CPU...")
    model = SentenceTransformer('BAAI/bge-m3', device='cpu')

    client = chromadb.PersistentClient(path=db_path)
    
    try:
        client.delete_collection(collection_name)
    except:
        pass
    
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    print(f"📖 Reading enriched chunks...")
    chunks = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            chunks.append(json.loads(line))

    texts = [c["text"] for c in chunks]
    ids = [c["id"] for c in chunks]
    metadatas = []
    
    for c in chunks:
        meta = {}
        for k, v in c["metadata"].items():
            if k == "chronology" and isinstance(v, dict):
                # FLATTEN CHRONOLOGY
                meta["chronology_personal"] = v.get("personal", False)
                meta["chronology_place"] = v.get("place", False)
            elif isinstance(v, (str, int, float, bool)):
                meta[k] = v
            elif isinstance(v, list):
                meta[k] = ", ".join(str(x) for x in v)
            elif v is None:
                meta[k] = ""
        metadatas.append(meta)

    batch_size = 32
    print(f"🧠 Computing embeddings and ingesting to ChromaDB ({len(texts)} chunks)...")
    
    for i in tqdm(range(0, len(texts), batch_size)):
        batch_texts = texts[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        batch_metadatas = metadatas[i:i+batch_size]
        
        batch_embeddings = model.encode(batch_texts, normalize_embeddings=True)
        
        collection.add(
            ids=batch_ids,
            embeddings=batch_embeddings.tolist(),
            documents=batch_texts,
            metadatas=batch_metadatas
        )

    print(f"✅ Embeddings computed (CPU) and persisted to collection '{collection_name}'")

if __name__ == "__main__":
    embed_micro_dataset()
