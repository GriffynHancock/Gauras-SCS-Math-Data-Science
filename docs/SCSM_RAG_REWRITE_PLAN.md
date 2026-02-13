# SCSM RAG Pipeline Rewrite Plan: Structural & Multi-Step Retrieval

## Phase 1: Structural Metadata Enrichment
**Goal**: Distinguish between Prose, Slokas, and Songs at the chunk level.
1.  **Sloka Detection**:
    *   Pattern: Non-English lines followed by `Translation` or numbered verses `(1)`, `(2)`, or citations like `(Śrīmad Bhagavad-gītā: 4.34)`.
    *   Action: Tag metadata `type: sloka` and `script: sanskrit/bengali`.
2.  **Song Integration**:
    *   Ingest `gaudiya_gitanjali` folder.
    *   Metadata: `category: song`, `author: (from folder name)`, `song_title: (from filename/header)`.
3.  **Prose Tagging**:
    *   Default `type: prose` for everything else.

## Phase 2: Advanced Chunking Strategy
**Goal**: Preserve logical units (Verse + Translation + Purport).
1.  **Greedy Grouping**:
    *   If a chunk starts with "Verse X" or a Sanskrit sloka, ensure the subsequent "Translation" and "Purport" elements are bonded into the same chunk or linked via `parent_id`.
2.  **Sequence ID**:
    *   Assign `sequence_index` to all chunks within a book to allow neighboring retrieval.

## Phase 3: 2-Step "Context Expansion" Retrieval
**Goal**: Provide the LLM with the full "Purport" even if only the "Verse" matched.
1.  **Step 1: Semantic Search**: Retrieve top-k chunks based on query.
2.  **Step 2: Neighborhood Fetch**:
    *   For each hit, retrieve `N` chunks before and after (using `sequence_index` and `book_id`).
    *   De-duplicate overlapping neighborhoods.
3.  **Aggregation**: Group results by `book_id` for the LLM prompt.

## Phase 4: Implementation of the "Expert RAG" Script
**Goal**: Create `expert_rag.py` which implements the 2-step logic and metadata filtering.
1.  **Filter Support**: Allow the user to specify `--only-slokas` or `--include-songs`.
2.  **Citation Engine 2.0**: Enhanced citations including verse numbers and song authors.

## Phase 1.2: Granular Type Taxonomy
**Goal**: Move beyond simple prose/sloka to functional types.
*   **Types**:
    *   `sloka`: The original Sanskrit/Bengali verse.
    *   `translation`: The direct English rendering of the sloka.
    *   `explanation`: Purports, commentaries, or direct expansions on a verse.
    *   `prose`: General narrative, historical accounts, or introductory text.
    *   `song_verse`: Specific verses from the Gaudiya Gitanjali.

## Phase 6: LLM Semantic Enrichment (Batch Processing)
**Goal**: Use an LLM to add "Divine Intelligence" to each chunk.
1.  **Entity Tagging**:
    *   Identify subjects: `Krishna`, `Radharani`, `Chaitanya Mahaprabhu`, `Nityananda Prabhu`, `Bhakti Vinod Thakur`, etc.
    *   Detect "Speaker" context where possible.
2.  **Canonical Transliteration**:
    *   For `sloka` chunks, generate a standardized IAST (International Alphabet of Sanskrit Transliteration) version in the `text_canonical` field.
3.  **Topic Scoring**:
    *   Assign scores (0.0 - 1.0) for top 3 topics from the global taxonomy.

## Phase 7: Expert Retrieval 2.0
**Goal**: Update `expert_rag.py` to utilize new metadata.
1.  **Cross-Lingual Match**: Search against both `text` and `text_canonical`.
2.  **Entity Filters**: Allow queries like "What does Govinda Maharaj say about *Radharani* in *Saranagati*?"
3.  **Balanced Results**: Ensure the 2-step retrieval picks up a `sloka` + `translation` + `explanation` triplet.
