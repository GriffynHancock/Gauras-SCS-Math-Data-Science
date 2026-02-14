import os
import json
import chromadb
import gc
import re
from pathlib import Path
from sentence_transformers import SentenceTransformer
from transformers import pipeline as transformers_pipeline
from tools.scripture_chunker import ScriptureChunker

class IngestionPipeline:
    def __init__(self, db_path, model_dir):
        self.db_path = db_path
        self.model_dir = model_dir
        self.client = chromadb.PersistentClient(path=db_path)
        self.embed_model_name = "BAAI/bge-m3" 
        self.encoder = None
        self.llm = None
        self.ner = None
        
        # Paths
        self.prompt_path = "/Users/gaura/scss/Attempt2/PROMPT.txt"
        self.halted_log_path = "data/processed/halted_chunks.log"
        
        try:
            with open(self.prompt_path, 'r', encoding='utf-8') as f:
                self.base_prompt = f.read()
        except Exception:
            self.base_prompt = "Extract metadata for Gaudiya Vaishnava literature."

    def load_model(self):
        """Loads Embedding Model."""
        if self.encoder is None:
            local_path = os.path.join(self.model_dir, "Qwen3-Embedding-4B")
            if not os.path.exists(local_path):
                local_path = os.path.join(os.path.dirname(self.model_dir), "Attempt2", "models", "Qwen3-Embedding-4B")
            
            if os.path.exists(local_path):
                print(f"Loading embedding model from local: {local_path}...")
                self.encoder = SentenceTransformer(local_path, device='cpu', trust_remote_code=True)
            else:
                print(f"Local model not found. Loading default: {self.embed_model_name}...")
                self.encoder = SentenceTransformer(self.embed_model_name, device='cpu')

    def unload_model(self):
        if self.encoder is not None:
            print("Unloading embedding model...")
            del self.encoder
            self.encoder = None
            gc.collect()

    def load_ner(self):
        if self.ner is None:
            ner_path = os.path.join(os.path.dirname(self.model_dir), "Attempt2", "models", "bert-large-NER")
            if os.path.exists(ner_path):
                print(f"Loading NER model...")
                self.ner = transformers_pipeline("ner", model=ner_path, tokenizer=ner_path, aggregation_strategy="simple")

    def unload_ner(self):
        if self.ner is not None:
            print("Unloading NER model...")
            del self.ner
            self.ner = None
            gc.collect()

    def load_llm(self):
        """Loads Jan LLM via llama.cpp with 500 token limit."""
        if self.llm is None:
            model_path = "/Users/gaura/Library/Application Support/Jan/data/llamacpp/models/Jan-v3-4b-base-instruct-Q8_0/model.gguf"
            print(f"Loading Jan-v3-4b LLM...")
            from llama_index.llms.llama_cpp import LlamaCPP
            self.llm = LlamaCPP(
                model_path=model_path,
                temperature=0.1,
                max_new_tokens=500, # Halts at 500 tokens
                context_window=4096, # Increased to prevent input truncation
                model_kwargs={"n_gpu_layers": -1},
                verbose=False,
            )

    def unload_llm(self):
        if self.llm is not None:
            print("Unloading LLM...")
            del self.llm
            self.llm = None
            gc.collect()

    def _create_gold_standard_chunk(self, id, text, metadata):
        base_metadata = {
            "book_id": "unknown",
            "title": "Unknown Title",
            "author": "Unknown Author",
            "chunk_index": 0,
            "type": None,
            "topics": [], 
            "entities": [],
            "has_sloka": False,
            "source_ref": [],
            "first_line_sloka": None,
            "summary": ""
        }
        base_metadata.update(metadata)
        return {"id": id, "text": text, "metadata": base_metadata}

    def ingest_songs(self, data_path):
        chunks = []
        path = Path(data_path)
        if path.exists():
            for file in path.glob("**/*.json"):
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    verse = data.get('verse', '')
                    translation = data.get('translation', '')
                    combined_text = f"{verse}\n{translation}".strip()
                    chunk_id = f"{data.get('title', 'song')}_{data.get('verse_number', 0)}"
                    metadata = {
                        "type": "song",
                        "title": data.get('title'),
                        "author": data.get('author'),
                        "chunk_index": data.get('verse_number', 0),
                        "has_sloka": True,
                        "first_line_sloka": ScriptureChunker.get_first_transliterated_line(verse)
                    }
                    chunks.append(self._create_gold_standard_chunk(chunk_id, combined_text, metadata))
        return chunks

    def ingest_books(self, data_path):
        chunks = []
        path = Path(data_path)
        if path.exists():
            for file in path.glob("**/*.txt"):
                with open(file, 'r', encoding='utf-8') as f:
                    text = f.read()
                book_id = file.stem
                if ScriptureChunker.is_scripture(file):
                    scripture_chunks = ScriptureChunker.generic_scripture_chunker(text, book_id)
                    for i, sc in enumerate(scripture_chunks):
                        chunk_id = f"{book_id}_{sc['verse_num']}_{sc['type']}"
                        metadata = {
                            "book_id": book_id,
                            "title": book_id.replace("en-", ""),
                            "chunk_index": i,
                            "type": sc['type'],
                            "has_sloka": True if sc['type'] == "verse+translation" else False,
                            "first_line_sloka": sc['first_line_sloka']
                        }
                        chunks.append(self._create_gold_standard_chunk(chunk_id, sc['text'], metadata))
                else:
                    metadata = {"book_id": book_id, "title": book_id.replace("en-", "")}
                    chunks.append(self._create_gold_standard_chunk(book_id, text[:2000], metadata))
        return chunks

    def _enrich_single_chunk(self, chunk):
        """Helper to enrich one chunk. Detects LLM halting."""
        if self.ner:
            try:
                ner_results = self.ner(chunk['text'][:1000])
                entities = list(set([res['word'] for res in ner_results if res['score'] > 0.8]))
                chunk['metadata']['entities'].extend(entities)
            except Exception: pass

        # LLM pass with full text (no truncation)
        full_prompt = f"{self.base_prompt}\n\n<input>\n{chunk['text']}\n</input>"
        response = self.llm.complete(full_prompt)
        
        # Check if halted (finish_reason in raw response if available)
        is_halted = False
        if hasattr(response, 'raw') and response.raw.get('choices'):
            if response.raw['choices'][0].get('finish_reason') == 'length':
                is_halted = True
        
        if is_halted:
            os.makedirs("data/processed", exist_ok=True)
            with open(self.halted_log_path, 'a', encoding='utf-8') as log:
                log.write(f"--- HALTED: {chunk['id']} ---\nOutput:\n{response.text}\n\n")

        try:
            text_resp = response.text
            match = re.search(r'<output>(.*?)</output>', text_resp, re.DOTALL)
            enrichment = json.loads(match.group(1).strip()) if match else {}
            
            if enrichment.get('entities'): chunk['metadata']['entities'].extend(enrichment['entities'])
            if enrichment.get('topics'): chunk['metadata']['topics'].extend(enrichment['topics'])
            if enrichment.get('source_ref'): chunk['metadata']['source_ref'].extend(enrichment['source_ref'])
            
            chunk['metadata']['entities'] = list(set(chunk['metadata']['entities']))
            chunk['metadata']['topics'] = list(set(chunk['metadata']['topics']))
            chunk['metadata']['source_ref'] = list(set(chunk['metadata']['source_ref']))
            
            if enrichment.get('type'): chunk['metadata']['type'] = enrichment['type']
            if enrichment.get('summary'): chunk['metadata']['summary'] = enrichment['summary']
            if 'has_sloka' in enrichment: chunk['metadata']['has_sloka'] = enrichment['has_sloka']
        except Exception as e:
            print(f"Error parsing {chunk['id']}: {e}")
        
        return chunk

    def validate_before_indexing(self, chunks):
        """Validates dataset integrity based on ATTEMPT2.md and safety guidelines."""
        print(f"🔍 Validating {len(chunks)} chunks before indexing...")
        
        # 1. Structural and Null Checks
        ids = []
        enriched_count = 0
        
        for i, chunk in enumerate(chunks):
            # Presence
            assert 'id' in chunk and chunk['id'], f"Chunk {i}: missing/empty id"
            assert 'text' in chunk and chunk['text'], f"Chunk {i}: missing/empty text"
            assert 'metadata' in chunk, f"Chunk {i}: missing metadata"
            
            m = chunk['metadata']
            # Type Safety for Chroma
            assert isinstance(m.get('topics'), list), f"{chunk['id']}: topics must be a list"
            assert isinstance(m.get('entities'), list), f"{chunk['id']}: entities must be a list"
            assert isinstance(m.get('source_ref'), list), f"{chunk['id']}: source_ref must be a list"
            assert isinstance(m.get('has_sloka'), bool), f"{chunk['id']}: has_sloka must be a boolean"
            
            # Null Poison Checks
            assert m.get('type') is not None, f"{chunk['id']}: type is None"
            assert m.get('book_id') is not None, f"{chunk['id']}: book_id is None"
            assert m.get('title') is not None, f"{chunk['id']}: title is None"
            
            # Progress Tracking
            if len(m.get('topics', [])) > 0 or len(m.get('entities', [])) > 0:
                enriched_count += 1
            
            ids.append(chunk['id'])

        # 2. Unique IDs
        assert len(ids) == len(set(ids)), f"Duplicate IDs found: {len(ids) - len(set(ids))} duplicates."
        
        # 3. Enrichment Rate (30% threshold)
        rate = enriched_count / len(chunks) if chunks else 0
        assert rate >= 0.3, f"Only {rate*100:.1f}% chunks enriched. Expected >= 30%."
        
        print(f"✅ Validation passed: {len(chunks)} chunks, {rate*100:.1f}% enriched.")
        return True

    def enrich_chunks(self, chunks, batch_size=10):
        state_file = "data/processed/enrichment_state.json"
        checkpoint_file = "data/processed/enriched_chunks.jsonl"
        os.makedirs("data/processed", exist_ok=True)

        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                start_idx = json.load(f).get('last_completed_index', -1) + 1
                print(f"📂 Resuming enrichment from chunk {start_idx}/{len(chunks)}")
        else:
            start_idx = 0
            if os.path.exists(checkpoint_file): os.remove(checkpoint_file)

        if start_idx >= len(chunks):
            return self.load_enriched_chunks(checkpoint_file)

        self.load_ner()
        self.load_llm()
        
        last_completed = start_idx - 1
        try:
            for i in range(start_idx, len(chunks)):
                chunk = chunks[i]
                print(f"[{i+1}/{len(chunks)}] Enriching {chunk['id']}...")
                enriched = self._enrich_single_chunk(chunk)
                with open(checkpoint_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(enriched, ensure_ascii=False) + '\n')
                last_completed = i
                if (i + 1) % batch_size == 0:
                    with open(state_file, 'w') as f:
                        json.dump({'last_completed_index': last_completed}, f)
        finally:
            with open(state_file, 'w') as f:
                json.dump({'last_completed_index': last_completed}, f)
            self.unload_ner()
            self.unload_llm()

        return self.load_enriched_chunks(checkpoint_file)

    def load_enriched_chunks(self, checkpoint_file="data/processed/enriched_chunks.jsonl"):
        enriched = []
        if os.path.exists(checkpoint_file):
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                for line in f:
                    enriched.append(json.loads(line))
        return enriched

    def build_index(self, chunks, collection_name):
        # Mandatory Validation
        self.validate_before_indexing(chunks)
        
        collection = self.client.get_or_create_collection(collection_name)
        ids = [c['id'] for c in chunks]
        documents = [c['text'] for c in chunks]
        metadatas = []
        for c in chunks:
            m = c['metadata'].copy()
            # Just handle None values - keep lists as lists
            for k, v in m.items():
                if v is None: m[k] = ""
            metadatas.append(m)
        
        self.load_model()
        try:
            embeddings = self.encoder.encode(documents).tolist()
        finally:
            self.unload_model()
        
        collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
        return collection
