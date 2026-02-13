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

### Phase 6: Real LLM Enrichment Status
*   **Infrastructure**: Built `llama.cpp` from source on M3 Mac; `llama-server` active on port 8080.
*   **Enrichment Harness**: Implemented `real_llm_enricher.py` using local Llama 3.1 8B Instruct.
*   **Verification**: Successfully processed 100 chunks with rich metadata (Entities, Topics, IAST Transliteration).
*   **Sample Metadata**:
    *   *Entities*: "Śrīla Bhakti Sundar Govinda Dev-Goswāmī Mahārāj", "Śrī Caitanya Sāraswat Maṭh".
    *   *Topics*: Guru-tattva (1.0), Saranagati (0.5).

### Next Steps
1.  **Bulk Enrichment**: Continue Phase 6 for the remaining 14,982 chunks (estimated time: ~100 hours at current rate, may need further parallelization or optimization).
2.  **Triplet Retrieval**: Update `ExpertRAGv2` to search against `text_canonical` and filter by entities.
3.  **UI/CLI Polish**: Add color-coded outputs for different theological types.
