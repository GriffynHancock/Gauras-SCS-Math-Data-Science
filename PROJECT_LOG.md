# Project Log: Gaudiya Vaishnava RAG Pipeline

## Status: Phase 1-5 Complete
The initial pipeline from raw text extraction to a functional vector database has been established.

### Completed Milestones
1.  **Environment Setup**: Configured `.venv311` with `chromadb`, `unstructured`, and `sentence-transformers`.
2.  **Canonical Normalization**: Implemented `canonical_normalize.py` to fix OCR artifacts and standardize diacritics (e.g., Śrīla, Kṛṣṇa).
3.  **Semantic Chunking**: Implemented `enrich_dataset.py` using `unstructured` to create 11,937 metadata-enriched chunks.
4.  **Vector Ingestion**: Implemented `ingest_to_chroma.py` to populate a persistent ChromaDB collection (`scsmath_rag`).
5.  **Basic Retrieval**: Implemented `scsmath_rag.py` for semantic search with citation support.

### Key Learnings from Initial Testing
*   **Retrieval Depth**: A query for "Saranagati" retrieved general prose but missed specific slokas and songs.
*   **Metadata Deficit**: The current system does not distinguish between "sloka" and "prose", nor does it handle the specific structure of the *Gitanjali* songs effectively.
*   **Context Fragmentation**: Semantic search occasionally returns a "Purport" without its corresponding "Verse", or vice-versa.

### Structural Refinement Status
*   **Positional Parsing**: Successfully extracted Chapter/Verse metadata for ~15k chunks using `structural_parser.py`.
*   **Taxonomy Initiation**: Sampled 100 chunks and identified 12 core theological topics (e.g., Guru-tattva, Rasa-tattva).
*   **Metadata Evolution**: Transitioning from basic chunking to "Rich Theological Chunks" with topic scores and dialogue detection.

### Phase 6.1: Expert Enrichment v3
*   **Refined Goal**: Process chunks individually with a simplified LLM prompt to identify entities, types (Sloka, Explanation, Prose), and scriptural sources.
*   **Infrastructure**: Using `llama-server` on port 8083 (CPU-only for stability during this test).
*   **Status**: Staging a 15-chunk verification run.

### Current RAG State
*   **Interface**: `expert_rag_v2.py` now supports "triplet" expansion (Verse + Translation + Purport).
*   **Quality Control**: Implemented stricter "garbage" filtering for URL-only or low-token chunks.
