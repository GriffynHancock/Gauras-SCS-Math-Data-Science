import chromadb
from sentence_transformers import SentenceTransformer
import numpy as np

def debug_rag():
    model = SentenceTransformer('BAAI/bge-m3')
    client = chromadb.PersistentClient(path="chroma_db")
    try:
        topics_col = client.get_collection("micro_topics_collection")
    except:
        print("❌ micro_topics_collection not found.")
        return
    
    queries = [
        "What is the nature of the soul?",
        "Who is Mahaprabhu?",
        "Tell me about the Holy Name.",
        "How to practice surrender?"
    ]
    
    count = topics_col.count()
    print(f"📊 Testing {len(queries)} queries against {count} topics...")
    
    for q in queries:
        print(f"\nQuery: '{q}'")
        q_emb = model.encode([q], normalize_embeddings=True).tolist()
        
        # Print first 5 dimensions of query embedding to see if they change
        print(f"  Q-Emb (first 5): {q_emb[0][:5]}")
        
        results = topics_col.query(
            query_embeddings=q_emb,
            n_results=3
        )
        
        if results['ids']:
            for i in range(len(results['ids'][0])):
                t_id = results['ids'][0][i]
                dist = results['distances'][0][i]
                label = results['metadatas'][0][i].get('label', 'N/A')
                print(f"  [{i+1}] {t_id} - {label} (Dist: {dist:.4f})")
        else:
            print("  No results found.")
        print("-" * 40)

    # Check topic embeddings themselves
    print("\n🔍 Inspecting Topic Embeddings:")
    all_topics = topics_col.get(include=['embeddings', 'metadatas'])
    if all_topics['ids']:
        for i in range(min(3, len(all_topics['ids']))):
            t_id = all_topics['ids'][i]
            emb = all_topics['embeddings'][i]
            label = all_topics['metadatas'][i].get('label', 'N/A')
            print(f"  {t_id} ({label}) - First 5: {emb[:5]}")
    else:
        print("  No topics found in collection.")

if __name__ == "__main__":
    debug_rag()
