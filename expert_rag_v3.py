import chromadb
from chromadb.utils import embedding_functions
import argparse

class ExpertRAGv3:
    def __init__(self, db_path="chroma_db", collection_name="scsmath_advanced"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.emb_fn = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_collection(
            name=collection_name,
            embedding_function=self.emb_fn
        )

    def query(self, text, n_results=5, entities=None, types=None):
        where_clause = {}
        filters = []
        if types:
            filters.append({"type": {"$in": types}})
            
        if len(filters) > 1:
            where_clause = {"$and": filters}
        elif len(filters) == 1:
            where_clause = filters[0]

        results = self.collection.query(
            query_texts=[text],
            n_results=n_results,
            where=where_clause if where_clause else None
        )
        return results

    def expand_context(self, initial_hits, initial_window=1):
        enriched_results = []
        seen_ids = set()

        for i in range(len(initial_hits['ids'][0])):
            meta = initial_hits['metadatas'][0][i]
            book_id = meta['book_id']
            idx = meta['chunk_index']
            
            start_idx = max(0, idx - initial_window)
            end_idx = idx + initial_window
            
            current_neighbors = self.fetch_range(book_id, start_idx, end_idx)
            
            while current_neighbors and current_neighbors[-1][2]['type'] == 'sloka':
                end_idx += 1
                new_chunk = self.fetch_range(book_id, end_idx, end_idx)
                if not new_chunk:
                    break
                current_neighbors.extend(new_chunk)
                if end_idx > idx + 10:
                    break

            content_blocks = []
            for n_id, n_doc, n_meta in current_neighbors:
                if n_id not in seen_ids:
                    # PRIORITIZE HAS_SLOKA BOOLEAN
                    is_sloka = n_meta.get('has_sloka', False) or n_meta.get('type') == 'sloka'
                    type_label = "SLOKA" if is_sloka else n_meta.get('category', n_meta.get('type', 'prose')).upper()
                    
                    ref = f" ({n_meta.get('chapter', '0')}.{n_meta.get('verse', '0')})" if 'verse' in n_meta else ""
                    block = f"[{type_label}] [ID: {n_id}]{ref}\n{n_doc}"
                    content_blocks.append(block)
                    seen_ids.add(n_id)

            if content_blocks:
                # CLEANER CITATION
                author = n_meta.get('author', 'Unknown')
                citation = n_meta['title']
                if author != "Unknown":
                    citation = f"{author}, {citation}"

                enriched_results.append({
                    "source": citation,
                    "content": "\n\n".join(content_blocks),
                    "relevance": 1 - initial_hits['distances'][0][i]
                })

        return enriched_results

    def fetch_range(self, book_id, start, end):
        results = self.collection.get(
            where={
                "$and": [
                    {"book_id": {"$eq": book_id}},
                    {"chunk_index": {"$gte": start}},
                    {"chunk_index": {"$lte": end}}
                ]
            }
        )
        zipped = list(zip(results['ids'], results['documents'], results['metadatas']))
        zipped.sort(key=lambda x: x[2]['chunk_index'])
        return zipped

def main():
    parser = argparse.ArgumentParser(description="Expert SCS Math RAG v3.0 (Dynamic Expansion)")
    parser.add_argument("query", help="Theological question")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--window", type=int, default=1, help="Initial neighborhood size")
    args = parser.parse_args()

    rag = ExpertRAGv3()
    
    print(f"🔍 Searching for: '{args.query}'...")
    initial = rag.query(args.query, n_results=args.top_k)
    final = rag.expand_context(initial, initial_window=args.window)

    print("\n" + "="*80)
    print("☸️  EXPERT THEOLOGICAL RETRIEVAL (v3.0)")
    print("="*80)

    for i, res in enumerate(final, 1):
        print(f"\n--- HIT {i} | {res['source']} (Rel: {res['relevance']:.2f}) ---")
        print(res['content'])
        print("-" * 80)

if __name__ == "__main__":
    main()
