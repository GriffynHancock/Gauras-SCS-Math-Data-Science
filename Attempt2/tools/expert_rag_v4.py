import argparse
import chromadb
import json
import sys
from pathlib import Path
from sentence_transformers import SentenceTransformer

class ExpertRAGv4:
    def __init__(self, db_path="chroma_db", collection_name="micro_chunks_collection", topics_name="micro_topics_collection"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.chunks_col = self.client.get_collection(collection_name)
        self.topics_col = self.client.get_collection(topics_name)
        
        print("🧠 Loading BGE-M3 (CPU)...")
        self.model = SentenceTransformer('BAAI/bge-m3', device='cpu')
        self.instruction = "Represent this sentence for searching relevant passages: "

    def query(self, text, n_topics=3, n_chunks=10, filters=None):
        # 1. Embed query
        query_emb = self.model.encode([self.instruction + text], normalize_embeddings=True).tolist()
        
        # 2. Topic Routing
        topic_hits = self.topics_col.query(
            query_embeddings=query_emb,
            n_results=n_topics
        )
        topic_ids = topic_hits['ids'][0]
        
        # 3. Chunk Retrieval with Filtering
        where_clause = {"topic_id": {"$in": topic_ids}}
        if filters:
            # Combine filters if multiple
            if len(filters) > 1:
                where_clause = {"$and": [where_clause] + filters}
            else:
                where_clause = {"$and": [where_clause, filters[0]]}
                
        chunk_hits = self.chunks_col.query(
            query_embeddings=query_emb,
            n_results=n_chunks,
            where=where_clause
        )
        
        return chunk_hits, topic_hits

    def expand_triplet(self, book_id, chunk_index, window=1):
        """Fetches neighboring chunks for context expansion"""
        start = max(0, chunk_index - window)
        end = chunk_index + window
        
        results = self.chunks_col.get(
            where={
                "$and": [
                    {"book_id": {"$eq": book_id}},
                    {"chunk_index": {"$gte": start}},
                    {"chunk_index": {"$lte": end}}
                ]
            }
        )
        
        # Sort by index
        zipped = list(zip(results['ids'], results['documents'], results['metadatas']))
        zipped.sort(key=lambda x: x[2]['chunk_index'])
        return zipped

    def format_output(self, chunk_hits, topic_hits):
        print("
" + "="*80)
        print("☸️  SCS MATH EXPERT RAG v4.0 (Topic-Centric Routing)")
        print("="*80)
        
        print("
📍 ROUTED TOPICS:")
        for i in range(len(topic_hits['ids'][0])):
            meta = topic_hits['metadatas'][0][i]
            dist = topic_hits['distances'][0][i]
            tags = []
            if meta.get('is_lila'): tags.append("LILA")
            if meta.get('chronology_personal'): tags.append("P-CHRONO")
            if meta.get('chronology_place'): tags.append("L-CHRONO")
            tag_str = f" [{', '.join(tags)}]" if tags else ""
            print(f"  - {meta['label']}{tag_str} (Score: {1-dist:.2f})")

        print("
📖 RETRIEVED BLOCKS:")
        seen_ids = set()
        for i in range(len(chunk_hits['ids'][0])):
            c_id = chunk_hits['ids'][0][i]
            if c_id in seen_ids: continue
            
            doc = chunk_hits['documents'][0][i]
            meta = chunk_hits['metadatas'][0][i]
            dist = chunk_hits['distances'][0][i]
            
            # Expansion (triplet)
            neighbors = self.expand_triplet(meta['book_id'], meta['chunk_index'])
            
            print(f"
--- HIT {i+1} | {meta.get('title')} | Score: {1-dist:.2f} ---")
            for n_id, n_doc, n_meta in neighbors:
                type_label = n_meta.get('type', 'prose').upper()
                print(f"[{type_label}] {n_doc}")
                seen_ids.add(n_id)
            print("-" * 80)

def main():
    parser = argparse.ArgumentParser(description="Expert RAG v4.0")
    parser.add_argument("query", help="Theological question")
    parser.add_argument("--lila", action="store_true", help="Filter for Divine Lila")
    parser.add_argument("--chrono", action="store_true", help="Filter for Historical/Chronological info")
    parser.add_argument("--author", type=str, help="Filter by author")
    args = parser.parse_args()

    rag = ExpertRAGv4()
    
    filters = []
    if args.lila: filters.append({"is_lila": {"$eq": True}})
    if args.chrono: filters.append({"chronology_personal": {"$eq": True}})
    if args.author: filters.append({"author": {"$eq": args.author}})
    
    chunks, topics = rag.query(args.query, filters=filters)
    rag.format_output(chunks, topics)

if __name__ == "__main__":
    main()
