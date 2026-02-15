"""
INGESTION & ENRICHMENT CONTROL FLOW (Step-by-Step):
1. INITIALIZATION: IngestionPipeline is initialized with paths for ChromaDB, local models, and a metadata extraction prompt (PROMPT.txt).
2. MODEL LOADING:
    - load_model(): Loads the BGE-M3 (or Qwen3) embedding model into memory on MPS (Mac) or CPU.
    - load_llm(): Loads a local Jan-v3-4b GGUF model via llama_index for metadata enrichment.
3. DATA INGESTION:
    - ingest_books(): Recursively finds .txt files. If recognized as scripture (via tools.scripture_chunker), it uses generic_scripture_chunker; otherwise, it uses split_into_normal_chunks.
    - ingest_songs(): Parses .json or .txt song files, combining verses and translations into single chunks.
    - _create_gold_standard_chunk(): Wraps raw text and basic metadata into a unified schema defined in ATTEMPT2.md.
4. METADATA ENRICHMENT:
    - enrich_chunks(): Iterates through raw chunks.
    - _enrich_single_chunk(): 
        a. Constructs a prompt using the base prompt + chunk text.
        b. Calls the local LLM to generate a JSON response.
        c. Uses regex to extract JSON from <output> tags.
        d. Updates the chunk's metadata (topics, entities, summary, etc.) with LLM-generated values.
    - Checkpointing: Saves enriched chunks to enriched_chunks.jsonl and progress to enrichment_state.json to allow resuming.
5. VALIDATION:
    - validate_before_indexing(): Performs structural, type, and "null poison" checks on the enriched dataset. Ensures at least 30% of chunks have been enriched.
6. INDEXING:
    - build_index(): 
        a. Flattens metadata lists (topics/entities) into comma-separated strings for ChromaDB compatibility.
        b. Encodes chunk text into vector embeddings using the loaded encoder.
        c. Adds IDs, documents, metadata, and embeddings to the ChromaDB collection.
7. MEMORY MANAGEMENT: Explicitly unloads models (unload_model/unload_llm) and calls gc.collect() to manage M3 Mac resources.
"""
import os
import json
import chromadb
import gc
import re
from pathlib import Path
from sentence_transformers import SentenceTransformer
from tools.scripture_chunker import ScriptureChunker
from tools.book_author_mapper import BookAuthorMapper

class IngestionPipeline:
    def __init__(self, db_path, model_dir):
        self.script_dir = Path(__file__).parent.absolute()
        self.db_path = db_path if os.path.isabs(db_path) else str(self.script_dir / db_path)
        self.model_dir = model_dir if os.path.isabs(model_dir) else str(self.script_dir / model_dir)
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.embed_model_name = "BAAI/bge-m3" 
        self.encoder = None
        self.llm = None
        self.author_mapper = BookAuthorMapper()
        
        # Paths
        self.prompt_path = str(self.script_dir / "PROMPT.txt")
        self.halted_log_path = str(self.script_dir / "data/processed/halted_chunks.log")
        
        try:
            with open(self.prompt_path, 'r', encoding='utf-8') as f:
                self.base_prompt = f.read()
        except Exception:
            self.base_prompt = "Extract metadata for Gaudiya Vaishnava literature."

    def load_model(self):
        """Loads Embedding Model."""
        if self.encoder is None:
            local_path = os.path.join(self.model_dir, "Qwen3-Embedding-4B")
            
            import torch
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
        from tools.song_chunker import SongChunker
        chunker = SongChunker()
        chunks = []
        path = Path(data_path)
        if path.exists():
            # Support both .json and .txt
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
            
            for file in path.glob("**/*.txt"):
                song_chunks = chunker.chunk_song(str(file))
                for sc in song_chunks:
                    metadata = {
                        "type": "song",
                        "title": sc['metadata'].get('title'),
                        "author": sc['metadata'].get('author'),
                        "chunk_index": sc['metadata'].get('verse_number', 0),
                        "has_sloka": True,
                        "first_line_sloka": ScriptureChunker.get_first_transliterated_line(sc['text'])
                    }
                    chunks.append(self._create_gold_standard_chunk(sc['id'], sc['text'], metadata))
        return chunks

    def ingest_books(self, data_path):
        chunks = []
        path = Path(data_path)
        if path.exists():
            for file in path.glob("**/*.txt"):
                with open(file, 'r', encoding='utf-8') as f:
                    text = f.read()
                book_id = file.stem
                author = self.author_mapper.get_author(file.name)
                if ScriptureChunker.is_scripture(file):
                    scripture_chunks = ScriptureChunker.generic_scripture_chunker(text, book_id)
                    for i, sc in enumerate(scripture_chunks):
                        chunk_id = f"{book_id}_{sc['verse_num']}_{sc['type']}"
                        metadata = {
                            "book_id": book_id,
                            "title": book_id.replace("en-", ""),
                            "author": author,
                            "chunk_index": i,
                            "type": sc['type'],
                            "has_sloka": True if sc['type'] == "verse+translation" else False,
                            "first_line_sloka": sc['first_line_sloka']
                        }
                        chunks.append(self._create_gold_standard_chunk(chunk_id, sc['text'], metadata))
                else:
                    # Proper chunking for normal books
                    normal_chunks = ScriptureChunker.split_into_normal_chunks(text)
                    for i, nc in enumerate(normal_chunks):
                        chunk_id = f"{book_id}_chunk_{i}"
                        metadata = {
                            "book_id": book_id, 
                            "title": book_id.replace("en-", ""),
                            "author": author,
                            "chunk_index": i,
                            "type": "prose"
                        }
                        chunks.append(self._create_gold_standard_chunk(chunk_id, nc, metadata))
        return chunks

    def _enrich_single_chunk(self, chunk):
        """Helper to enrich one chunk. Detects LLM halting."""
        # NER disabled due to non-functionality
        # if self.ner:
        #     try:
        #         ner_results = self.ner(chunk['text'][:1000])
        #         entities = list(set([res['word'] for res in ner_results if res['score'] > 0.8]))
        #         chunk['metadata']['entities'].extend(entities)
        #     except Exception: pass

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
            
            if enrichment.get('type') and chunk['metadata']['type'] is None: chunk['metadata']['type'] = enrichment['type']
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
            # Flatten lists to comma-separated strings for Chroma compatibility
            for k, v in m.items():
                if isinstance(v, list):
                    m[k] = ", ".join(map(str, v))
                elif v is None:
                    m[k] = ""
            metadatas.append(m)
        
        self.load_model()
        try:
            print(f"Encoding {len(documents)} documents (batch_size=4)...")
            embeddings = self.encoder.encode(documents, batch_size=4, show_progress_bar=True).tolist()
            print("Encoding complete.")
        finally:
            self.unload_model()
        
        collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
        return collection
