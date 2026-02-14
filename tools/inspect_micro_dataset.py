import chromadb
import random
import json

def inspect_micro_dataset():
    client = chromadb.PersistentClient(path="chroma_db")
    try:
        collection = client.get_collection("micro_chunks_collection")
    except Exception as e:
        print(f"❌ Collection not found: {e}")
        return
    
    count = collection.count()
    if count == 0:
        print("❌ Collection is empty.")
        return

    print(f"🔍 Inspecting 3 random chunks from {count} total...")
    
    # Get all IDs
    result = collection.get()
    ids = result['ids']
    
    if len(ids) < 3:
        sample_ids = ids
    else:
        sample_ids = random.sample(ids, 3)
    
    samples = collection.get(ids=sample_ids)
    
    for i in range(len(sample_ids)):
        print(f"\n--- Chunk {sample_ids[i]} ---")
        meta = samples['metadatas'][i]
        
        print(f"Type: {meta.get('type', 'N/A')}")
        print(f"Category: {meta.get('category', 'N/A')}")
        # Entities are strings in Chroma metadata now
        print(f"Entities: {meta.get('entities', '[]')}") 
        print(f"Summary: {meta.get('summary', 'N/A')}")
        
        doc = samples['documents'][i]
        preview = doc[:500] + "..." if len(doc) > 500 else doc
        print(f"\nText:\n{preview}")
        print("-" * 60)

if __name__ == "__main__":
    inspect_micro_dataset()
