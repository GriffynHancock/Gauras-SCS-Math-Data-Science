"""
RAG RETRIEVAL & LLM GENERATION CONTROL FLOW (Step-by-Step):
1. INITIALIZATION: RAGPipeline is initialized with paths to the ChromaDB directory and the local model directory.
2. QUERY EXECUTION (query method):
    - STAGE 1: SEMANTIC SEARCH
        a. load_model(): Loads the embedding encoder (BGE-M3 or Qwen3).
        b. encode(): Converts the user query into a vector embedding.
        c. unload_model(): Immediately frees embedding model memory.
        d. collection.query(): Performs a vector similarity search in ChromaDB to retrieve the top 'n_results' (e.g., top 10).
    - STAGE 2: RERANKING (NEW)
        a. load_reranker(): Loads the Qwen3-Reranker-4B model and tokenizer.
        b. format_pairs(): Pairs the query with each retrieved document using a specialized instruction prompt.
        c. compute_scores(): Passes pairs through the reranker LLM. It looks at the logits for 'yes' vs 'no' tokens at the end of the thought process to calculate a relevance score.
        d. sort(): Re-orders the initial results based on these high-fidelity reranker scores.
        e. filter(): Selects the top 'final_k' (e.g., top 3) most relevant documents.
    - STAGE 3: CONTEXT SYNTHESIS
        a. load_llm(): Loads the Jan-v3-4b synthesis LLM via llama_index.
        b. Context Assembly: Concatenates the reranked documents into a single "context" string.
        c. Prompt Engineering: Wraps the context and question in an "Expert Gaudiya Vaishnava theologian" persona prompt.
        d. llm.complete(): Sends the prompt to the local LLM.
        e. Result Construction: Returns a dictionary containing the answer, sources, and metadata.
3. MEMORY MANAGEMENT: Uses unload_model() and unload_llm() with gc.collect() between stages to ensure only one large model (4B-8B) is active in the M3 Mac's unified memory at a time.
"""
import os
import chromadb
import gc
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM

class RAGPipeline:
    def __init__(self, db_path, model_dir):
        from pathlib import Path
        self.script_dir = Path(__file__).parent.absolute()
        self.db_path = db_path if os.path.isabs(db_path) else str(self.script_dir / db_path)
        self.model_dir = model_dir if os.path.isabs(model_dir) else str(self.script_dir / model_dir)
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.embed_model_name = "BAAI/bge-m3" 
        self.encoder = None
        self.llm = None
        self.reranker_model = None
        self.reranker_tokenizer = None

    def load_model(self):
        if self.encoder is None:
            local_path = os.path.join(self.model_dir, "Qwen3-Embedding-4B")
            device = 'mps' if torch.backends.mps.is_available() else 'cpu'
            if os.path.exists(local_path):
                print(f"Loading embedding model from local: {local_path} on {device}...")
                self.encoder = SentenceTransformer(local_path, device=device, trust_remote_code=True)
            else:
                print(f"Local model not found at {local_path}. Loading default: {self.embed_model_name} on {device}...")
                self.encoder = SentenceTransformer(self.embed_model_name, device=device)

    def unload_model(self):
        if self.encoder is not None:
            print("Unloading embedding model...")
            del self.encoder
            self.encoder = None
            gc.collect()

    def load_reranker(self):
        if self.reranker_model is None:
            model_path = os.path.join(self.model_dir, "Qwen3-Reranker-4B")
            print(f"Loading Reranker model from {model_path}...")
            self.reranker_tokenizer = AutoTokenizer.from_pretrained(model_path, padding_side='left')
            self.reranker_model = AutoModelForCausalLM.from_pretrained(
                model_path, 
                torch_dtype=torch.float16 if torch.backends.mps.is_available() else torch.float32,
                device_map="auto"
            ).eval()

    def unload_reranker(self):
        if self.reranker_model is not None:
            print("Unloading Reranker...")
            del self.reranker_model
            del self.reranker_tokenizer
            self.reranker_model = None
            self.reranker_tokenizer = None
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
                context_window=4096,
                generate_kwargs={"stop": ["Question:", "Context:"]},
                model_kwargs={"n_gpu_layers": -1},
                verbose=False,
            )

    def unload_llm(self):
        if self.llm is not None:
            print("Unloading LLM...")
            del self.llm
            self.llm = None
            gc.collect()

    def _compute_rerank_scores(self, query, documents, metadatas, instruction):
        self.load_reranker()
        tokenizer = self.reranker_tokenizer
        model = self.reranker_model
        
        token_false_id = tokenizer.convert_tokens_to_ids("no")
        token_true_id = tokenizer.convert_tokens_to_ids("yes")
        max_length = 4096 # Reduced from 8192 for M3 memory
        
        prefix = "<|im_start|>system\nJudge whether the Document provides a substantive and informative answer to the Query based on the Instruct provided. Note that the answer can only be \"yes\" or \"no\". Documents that are merely titles, tables of contents, or introductory boilerplate should be marked as \"no\".<|im_end|>\n<|im_start|>user\n"
        suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
        prefix_tokens = tokenizer.encode(prefix, add_special_tokens=False)
        suffix_tokens = tokenizer.encode(suffix, add_special_tokens=False)

        scores = []
        for i, (doc, meta) in enumerate(zip(documents, metadatas)):
            print(f"  [Rerank {i+1}/{len(documents)}] Scoring document...")
            
            # Combine text with metadata for better context in reranking
            full_text_for_rerank = f"Book: {meta.get('title', 'Unknown')}\nAuthor: {meta.get('author', 'Unknown')}\nContent: {doc}"
            
            # Heuristic penalty for Table of Contents or very short metadata
            is_toc = doc.count("\n") > 8 and ("---" in doc or "..." in doc or "Contents" in doc)
            # Short docs that might be boilerplate, but if they mention the query subject, we should be careful
            is_metadata = len(doc.split()) < 40 and ("Maharaj" in doc or "Math" in doc) and query.lower() not in doc.lower()
            
            formatted = f"<Instruct>: {instruction}\n<Query>: {query}\n<Document>: {full_text_for_rerank}"
            inputs = tokenizer(
                [formatted], padding=False, truncation='longest_first',
                return_attention_mask=False, max_length=max_length - len(prefix_tokens) - len(suffix_tokens)
            )
            input_ids = prefix_tokens + inputs['input_ids'][0] + suffix_tokens
            input_tensor = torch.tensor([input_ids]).to(model.device)
            
            with torch.no_grad():
                logits = model(input_tensor).logits[:, -1, :]
                true_logit = logits[:, token_true_id]
                false_logit = logits[:, token_false_id]
                
                # Use a small epsilon to avoid log(0)
                # Actually log_softmax is better
                batch_scores = torch.stack([false_logit, true_logit], dim=1)
                batch_scores = torch.nn.functional.log_softmax(batch_scores, dim=1)
                score = batch_scores[:, 1].exp().item()
                
                # Apply heuristic penalty if identified as TOC/Metadata
                if is_toc:
                    score *= 0.05
                elif is_metadata:
                    score *= 0.2
                
                # Boost if the query term is present in a substantive way (e.g. many times)
                # query_count = doc.lower().count(query.lower().split()[-1]) # last word of query
                # if query_count > 3:
                #     score = min(1.0, score * 1.2)
                
                scores.append(score)
                gc.collect()
        
        return scores

    def query(self, text, collection_name="test_collection", n_initial=15, n_final=3, synthesize=True):
        try:
            collection = self.client.get_collection(collection_name)
        except ValueError:
            return "Collection not found. Please run ingestion first."
            
        # 1. Semantic Retrieval
        self.load_model()
        try:
            query_emb = self.encoder.encode([text]).tolist()
        finally:
            self.unload_model()
        
        initial_results = collection.query(
            query_embeddings=query_emb,
            n_results=n_initial
        )
        
        docs = initial_results['documents'][0]
        metas = initial_results['metadatas'][0]
        
        # 2. Reranking
        print(f"Reranking {len(docs)} candidates...")
        # Update instruction for better directness
        instruction = 'Identify documents that provide a direct, substantive theological explanation or characterization of the subject in the query. Prioritize definitions, philosophical mission statements, and core attributes. Exclude documents that are mere mentions, structural lists, or general relief work descriptions unless they specifically define the subject.'
        
        try:
            rerank_scores = self._compute_rerank_scores(text, docs, metas, instruction)
            # Zip and sort by score descending
            combined = list(zip(docs, metas, rerank_scores))
            combined.sort(key=lambda x: x[2], reverse=True)
            
            # Select top n_final
            final_selection = combined[:n_final]
            final_docs = [x[0] for x in final_selection]
            final_metas = [x[1] for x in final_selection]
            final_scores = [x[2] for x in final_selection]
        finally:
            self.unload_reranker()

        if not synthesize:
            return {"documents": final_docs, "metadatas": final_metas, "scores": final_scores}

        # 3. Synthesis
        self.load_llm()
        try:
            # Injecting speaker context as these are all from Sridhar Maharaj's books
            context_blocks = []
            for d, m in zip(final_docs, final_metas):
                block = f"Source: {m.get('title', 'Unknown')}\nSpeaker: Srila B.R. Sridhar Maharaj\nContent: {d}"
                context_blocks.append(block)
                
            context = "\n---\n".join(context_blocks)
            prompt = f"""You are an expert Gaudiya Vaishnava theologian specializing in the teachings of Srila B.R. Sridhar Maharaj. 
Answer the user question based ONLY on the provided context. 
If the information is not in the context, say you don't know.
Do not hallucinate additional questions or context labels.

Context:
{context}

Question: {text}
Answer:"""
            response = self.llm.complete(prompt)
            return {
                "answer": response.text,
                "source_documents": final_docs,
                "source_metadata": final_metas,
                "source_scores": final_scores
            }
        finally:
            self.unload_llm()
