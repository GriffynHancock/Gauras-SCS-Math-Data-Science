import os
import chromadb
import gc
from sentence_transformers import SentenceTransformer

class RAGPipeline:
    def __init__(self, db_path, model_dir):
        self.db_path = db_path
        self.model_dir = model_dir
        self.client = chromadb.PersistentClient(path=db_path)
        self.embed_model_name = "BAAI/bge-m3" 
        self.encoder = None
        self.llm = None

    def load_model(self):
        if self.encoder is None:
            local_path = os.path.join(self.model_dir, "Qwen3-Embedding-4B")
            if os.path.exists(local_path):
                print(f"Loading embedding model from local: {local_path}...")
                self.encoder = SentenceTransformer(local_path, device='cpu', trust_remote_code=True)
            else:
                print(f"Local model not found at {local_path}. Loading default: {self.embed_model_name}...")
                self.encoder = SentenceTransformer(self.embed_model_name, device='cpu')

    def unload_model(self):
        if self.encoder is not None:
            print("Unloading embedding model...")
            del self.encoder
            self.encoder = None
            gc.collect()

    def load_llm(self):
        if self.llm is None:
            model_path = "/Users/gaura/Library/Application Support/Jan/data/llamacpp/models/Jan-v3-4b-base-instruct-Q8_0/model.gguf"
            print(f"Loading Jan-v3-4b LLM for RAG synthesis...")
            from llama_index.llms.llama_cpp import LlamaCPP
            self.llm = LlamaCPP(
                model_path=model_path,
                temperature=0.7,
                max_new_tokens=512,
                context_window=2048,
                generate_kwargs={},
                model_kwargs={"n_gpu_layers": -1}, # Use Metal on M3
                verbose=False,
            )

    def unload_llm(self):
        if self.llm is not None:
            print("Unloading LLM...")
            del self.llm
            self.llm = None
            gc.collect()

    def query(self, text, collection_name="test_collection", n_results=3, synthesize=True):
        try:
            collection = self.client.get_collection(collection_name)
        except ValueError:
            return "Collection not found. Please run ingestion first."
            
        self.load_model()
        try:
            query_emb = self.encoder.encode([text]).tolist()
        finally:
            self.unload_model()
        
        results = collection.query(
            query_embeddings=query_emb,
            n_results=n_results
        )
        
        if not synthesize:
            return results

        # Synthesis
        self.load_llm()
        try:
            context = "\n---\n".join(results['documents'][0])
            prompt = f"""You are an expert Gaudiya Vaishnava theologian. 
Answer the user question based ONLY on the provided context.

Context:
{context}

Question: {text}
Answer:"""
            response = self.llm.complete(prompt)
            return {
                "answer": response.text,
                "source_documents": results['documents'][0],
                "source_metadata": results['metadatas'][0]
            }
        finally:
            self.unload_llm()
