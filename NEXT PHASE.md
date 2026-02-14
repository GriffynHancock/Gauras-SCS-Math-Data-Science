# Topic-Centroid Routing Pipeline - Status & Revised Plan

## CURRENT STATUS: Phase 1-9 (Micro-Test) SUCCESSFUL
The architecture has been proven on a representative micro-dataset (270 book chunks + 35 song chunks).

### Recent Achievements:
- **Manual Song Chunking**: Implemented `SongChunker` to cleanly pair Sloka + Translation as discrete chunks with verse numbers.
- **Theological Meta-Tags**: Added `is_lila`, `chronology_personal`, and `chronology_place` to the LLM enrichment prompt.
- **Signal Aggregation**: Topics now inherit these tags (e.g., `[LILA] [P-CHRONO]`) based on cluster density.
- **Hardware Stability**: Switched to CPU-only embeddings (`BGE-M3`) to avoid M3 Mac `MPS` memory/silent-failure issues.
- **Instructional Retrieval**: Implemented BGE-specific instruction prefixes for query embeddings, greatly improving relevance.

---

## PHASE 10: SCALE TO PRODUCTION (Current Focus)

### Step 10.1: Full Dataset Re-Enrichment
Apply the `MicroDatasetEnricher` logic to the complete 14,000+ chunk dataset.
- **Tool**: `tools/enrich_full_dataset.py` (to be created, based on `tools/enrich_micro_dataset.py`).
- **Constraint**: Needs to handle rate-limiting/timeouts for local LLM (est. 15-20 hours).
- **Update**: Use the v3.3 Tagger Prompt with Lila/Chrono signals.

### Step 10.2: Manual Song Processing
Process the entire `gaudiya_gitanjali` directory using the `SongChunker`.
- **Tool**: `tools/chunk_songs_full.py`.

### Step 10.3: Full Embedding & Topic Build
- Re-embed everything on CPU.
- Run HDBSCAN/UMAP on the full 15k+ dataset (expecting 100-200 topics).
- Perform LLM labeling on all discovered topics.

---

## PHASE 11: ADVANCED ROUTING & RAG v4

### Step 11.1: Expert Routing Logic
- Implement `ExpertRAGv4` which uses:
    - Topic-routing (from Phase 10).
    - Metadata filtering (by `is_lila`, `type`, `author`).
    - Dynamic Context Expansion (Verse + Translation + Purport "triplets").

### Step 11.2: Citations & Links
- Ensure every retrieval hit links back to the original source text or external URL where possible.

---

## PHASE 12: DEPLOYMENT & CLI

### Step 12.1: Production CLI
- Finalize `expert_rag.py` as the primary user interface.
- Add support for query-time filters (e.g., `--only-lila`, `--author "Srila Sridhar Maharaj"`).

### Step 12.2: Documentation & Export
- Finalize `PROJECT_SUMMARY.md`.
- Export the ChromaDB as a portable artifact.

---

**Notes from Phase 9/10 Work:**
- Do NOT use `MPS` for `BGE-M3` on this machine; it produces zero vectors silently.
- HDBSCAN `min_cluster_size` should be increased for the full dataset (try 5-10).
- UMAP `n_neighbors` should be increased for larger datasets (try 30).
