import chromadb
from chromadb.utils import embedding_functions
import argparse

class ExpertRAGv2:
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
        if entities:
            # entities are stored as comma-separated strings in this collection
            # Using $contains logic or iterating. Chroma $in usually expects exact match for string.
            pass 
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

    def expand_triplets(self, initial_hits, window=3):
        enriched_results = []
        seen_ids = set()

        for i in range(len(initial_hits['ids'][0])):
            meta = initial_hits['metadatas'][0][i]
            book_id = meta['book_id']
            idx = meta['chunk_index']
            
            neighbors = self.collection.get(
                where={
                    "$and": [
                        {"book_id": {"$eq": book_id}},
                        {"chunk_index": {"$gte": max(0, idx - window)}},
                        {"chunk_index": {"$lte": idx + window}}
                    ]
                }
            )

            zipped = list(zip(neighbors['ids'], neighbors['documents'], neighbors['metadatas']))
            zipped.sort(key=lambda x: x[2]['chunk_index'])

            content_blocks = []
            for n_id, n_doc, n_meta in zipped:
                if n_id not in seen_ids:
                    type_label = n_meta['type'].upper()
                    ref = f" ({n_meta.get('chapter', '0')}.{n_meta.get('verse', '0')})" if 'verse' in n_meta else ""
                    content_blocks.append(f"[{type_label}]{ref}\n{n_doc}")
                    seen_ids.add(n_id)

            if content_blocks:
                enriched_results.append({
                    "source": f"{n_meta.get('author', 'Unknown')}, {n_meta['title']}",
                    "content": "\n\n".join(content_blocks),
                    "relevance": 1 - initial_hits['distances'][0][i]
                })

        return enriched_results

def main():
    parser = argparse.ArgumentParser(description="Expert SCS Math RAG v2.0")
    parser.add_argument("query", help="Theological question")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--entity", action='append')
    parser.add_argument("--type", action='append')
    args = parser.parse_args()

    rag = ExpertRAGv2()
    
    initial = rag.query(args.query, n_results=args.top_k, entities=args.entity, types=args.type)
    final = rag.expand_triplets(initial)

    print("\n" + "="*80)
    print("☸️  EXPERT THEOLOGICAL RETRIEVAL (v2.0)")
    print("="*80)

    for i, res in enumerate(final, 1):
        print(f"\n--- HIT {i} | {res['source']} (Rel: {res['relevance']:.2f}) ---")
        print(res['content'])
        print("-" * 80)

if __name__ == "__main__":
    main()
