import argparse
import chromadb
from sentence_transformers import SentenceTransformer

def micro_rag(query, top_k_topics=3, top_k_chunks=10):
    print(f"🔎 Query: '{query}'")
    
    # 1. Embed Query
    model = SentenceTransformer('BAAI/bge-m3', device='cpu')
    instruction = "Represent this sentence for searching relevant passages: "
    query_embedding = model.encode([instruction + query], normalize_embeddings=True).tolist()

    client = chromadb.PersistentClient(path="chroma_db")
    try:
        topics_col = client.get_collection("micro_topics_collection")
        chunks_col = client.get_collection("micro_chunks_collection")
    except Exception as e:
        print(f"❌ Error getting collections: {e}")
        return

    # 2. Find Relevant Topics
    topic_results = topics_col.query(
        query_embeddings=query_embedding,
        n_results=top_k_topics
    )
    
    topic_ids = []
    print("\n" + "="*80)
    print("📍 ROUTED THEOLOGICAL TOPICS")
    print("="*80)
    
    if topic_results['ids'] and len(topic_results['ids'][0]) > 0:
        for i in range(len(topic_results['ids'][0])):
            t_id = topic_results['ids'][0][i]
            meta = topic_results['metadatas'][0][i]
            score = topic_results['distances'][0][i]
            
            flags = []
            if meta.get('is_lila'): flags.append("LILA")
            if meta.get('chronology_personal'): flags.append("P-CHRONO")
            if meta.get('chronology_place'): flags.append("L-CHRONO")
            flag_str = f" [{', '.join(flags)}]" if flags else ""
            
            print(f"[{i+1}] {meta.get('label', t_id)}{flag_str}")
            print(f"    Desc: {meta.get('description', 'N/A')}")
            print(f"    Keywords: {meta.get('keywords', 'N/A')}")
            topic_ids.append(t_id)
    
    # 3. Retrieve Chunks
    where_clause = {"topic_id": {"$in": topic_ids}}
    chunk_results = chunks_col.query(
        query_embeddings=query_embedding,
        n_results=top_k_chunks,
        where=where_clause
    )

    print("\n" + "="*80)
    print("📖 CANONICAL THEOLOGICAL BLOCKS")
    print("="*80)

    if chunk_results['ids'] and len(chunk_results['ids'][0]) > 0:
        for i in range(len(chunk_results['ids'][0])):
            c_id = chunk_results['ids'][0][i]
            doc = chunk_results['documents'][0][i]
            meta = chunk_results['metadatas'][0][i]
            dist = chunk_results['distances'][0][i]
            
            # Extract Rich Metadata
            book = meta.get('title', 'Unknown Book')
            author = meta.get('author', 'Unknown Author')
            category = meta.get('category', meta.get('type', 'prose')).upper()
            src = meta.get('scripture_source', 'Direct Instruction')
            entities = meta.get('entities', 'None')
            has_sloka = "💠 CONTAINS SLOKA" if meta.get('has_sloka') else ""
            
            lila = " [LILA]" if meta.get('is_lila') else ""
            chrono = ""
            if meta.get('chronology_personal'): chrono += " [P-CHRONO]"
            if meta.get('chronology_place'): chrono += " [L-CHRONO]"

            print(f"\n--- HIT {i+1} | {book} | {author} ---")
            print(f"ID: {c_id} | Score: {1-dist:.4f}")
            print(f"Ontology: {category} | Source: {src} {lila}{chrono}")
            if has_sloka: print(f"    {has_sloka}")
            print(f"Entities: {entities}")
            print(f"Summary: {meta.get('summary', 'N/A')}")
            print(f"\nText:\n{doc}")
            print("-" * 80)
    else:
        print("⚠️ No chunks found.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Expert RAG v4.1 (Canonical Reporting)")
    parser.add_argument("query", type=str, help="The query string")
    args = parser.parse_args()
    micro_rag(args.query)
