import chromadb
from chromadb.utils import embedding_functions
import argparse
from collections import defaultdict

class ExpertRAG:
    def __init__(self, db_path="chroma_db", collection_name="scsmath_advanced"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.emb_fn = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_collection(
            name=collection_name,
            embedding_function=self.emb_fn
        )

    def semantic_search(self, query, n_results=5, type_filter=None):
        where_clause = {}
        if type_filter:
            where_clause["type"] = type_filter
            
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_clause if where_clause else None
        )
        return results

    def expand_context(self, initial_hits, window_size=2):
        """Step 2: Neighborhood Fetch."""
        expanded_results = []
        seen_ids = set()

        for i in range(len(initial_hits['ids'][0])):
            hit_id = initial_hits['ids'][0][i]
            meta = initial_hits['metadatas'][0][i]
            book_id = meta['book_id']
            idx = meta['chunk_index']

            # Define range for neighborhood
            start_idx = max(0, idx - window_size)
            end_idx = idx + window_size
            
            # Retrieve neighboring chunks for this specific book
            neighbors = self.collection.get(
                where={
                    "$and": [
                        {"book_id": {"$eq": book_id}},
                        {"chunk_index": {"$gte": start_idx}},
                        {"chunk_index": {"$lte": end_idx}}
                    ]
                }
            )

            # Sort neighbors by chunk index to maintain flow
            zipped = list(zip(neighbors['ids'], neighbors['documents'], neighbors['metadatas']))
            zipped.sort(key=lambda x: x[2]['chunk_index'])

            neighborhood_text = []
            for n_id, n_doc, n_meta in zipped:
                if n_id not in seen_ids:
                    # Mark as seen to avoid duplication if multiple hits are close
                    prefix = f"[{n_meta['type'].upper()}]"
                    neighborhood_text.append(f"{prefix}\n{n_doc}")
                    seen_ids.add(n_id)

            if neighborhood_text:
                expanded_results.append({
                    "book_title": meta['title'],
                    "author": meta['author'],
                    "content": "\n\n".join(neighborhood_text),
                    "relevance": 1 - initial_hits['distances'][0][i]
                })

        return expanded_results

def main():
    parser = argparse.ArgumentParser(description="Expert SCS Math RAG")
    parser.add_argument("query", help="Theological question")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--window", type=int, default=2, help="Chunks to grab around each hit")
    parser.add_argument("--type", choices=['prose', 'sloka', 'song_verse'], help="Filter by type")
    args = parser.parse_args()

    rag = ExpertRAG()
    
    print(f"🔍 Searching for: '{args.query}'...")
    initial_hits = rag.semantic_search(args.query, n_results=args.top_k, type_filter=args.type)
    
    print(f"expanding context (window={args.window})...")
    final_results = rag.expand_context(initial_hits, window_size=args.window)

    print("\n" + "="*80)
    print("📚 ENRICHED THEOLOGICAL CONTEXT")
    print("="*80)

    for i, res in enumerate(final_results, 1):
        print(f"\n--- SOURCE {i}: {res['author']}, \"{res['book_title']}\" (Rel: {res['relevance']:.2f}) ---")
        print(res['content'])
        print("-" * 80)

    print("\n✅ Instructions for LLM:")
    print("Please synthesize the above verses and explanations to provide a comprehensive answer.")

if __name__ == "__main__":
    main()
