import chromadb
import numpy as np

def find_zero_embeddings():
    client = chromadb.PersistentClient(path="chroma_db")
    try:
        chunks_col = client.get_collection("micro_chunks_collection")
    except:
        print("❌ Collection not found.")
        return
    
    data = chunks_col.get(include=['embeddings', 'metadatas'])
    ids = data['ids']
    embeddings = np.array(data['embeddings'])
    metadatas = data['metadatas']
    
    zero_mask = np.all(embeddings == 0, axis=1)
    zero_indices = np.where(zero_mask)[0]
    
    print(f"🕵️ Found {len(zero_indices)} chunks with zero embeddings out of {len(ids)} total.")
    
    if len(zero_indices) > 0:
        print("\nSample zero-embedding chunks:")
        for i in range(min(10, len(zero_indices))):
            idx = zero_indices[i]
            z_id = ids[idx]
            meta = metadatas[idx]
            print(f"  - {z_id} (Book: {meta.get('book_id')}, Type: {meta.get('type')})")

if __name__ == "__main__":
    find_zero_embeddings()
