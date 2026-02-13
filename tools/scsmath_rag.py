import chromadb
from chromadb.utils import embedding_functions
import argparse

class SCSMathRAG:
    def __init__(self, db_path="chroma_db"):
        self.client = chromadb.PersistentClient(path=db_path)
        self.emb_fn = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_collection(
            name="scsmath_rag",
            embedding_function=self.emb_fn
        )

    def query(self, text, n_results=5):
        results = self.collection.query(
            query_texts=[text],
            n_results=n_results
        )
        return results

    def format_results(self, results):
        formatted = []
        for i in range(len(results['documents'][0])):
            doc = results['documents'][0][i]
            meta = results['metadatas'][0][i]
            dist = results['distances'][0][i]
            
            citation = f"{meta['author']}, \"{meta['title']}\" (Chunk {meta['chunk_index']})"
            formatted.append({
                "text": doc,
                "citation": citation,
                "relevance": 1 - dist
            })
        return formatted

def main():
    parser = argparse.ArgumentParser(description="SCS Math RAG Query Tool")
    parser.add_argument("query", help="The theological question to ask")
    parser.add_argument("--top-k", type=int, default=3, help="Number of results to retrieve")
    args = parser.parse_args()

    rag = SCSMathRAG()
    results = rag.query(args.query, n_results=args.top_k)
    formatted = rag.format_results(results)

    print("\n🔍 TOP RETRIEVED CONTEXTS:")
    print("=" * 80)
    for i, res in enumerate(formatted, 1):
        print(f"\n[{i}] RELEVANCE: {res['relevance']:.2f}")
        print(f"SOURCE: {res['citation']}")
        print("-" * 40)
        print(res['text'])
        print("-" * 80)

    print("\n💡 PROMPT FOR LLM:")
    print("Use the above context to answer the user's question accurately with citations.")

if __name__ == "__main__":
    main()
