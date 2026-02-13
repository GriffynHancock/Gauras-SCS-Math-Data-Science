# RAG Structure & Control Flow Analysis (v2.0)

## 1. Retrieval Logic: The "Expert" Flow
The `ExpertRAGv2` system follows a two-stage retrieval process designed specifically for highly structured theological texts.

### Stage 1: Semantic Discovery
- **Input**: User's natural language query.
- **Process**: ChromaDB performs a cosine similarity search on the vector embeddings.
- **Output**: A list of `top-k` discrete "anchor" chunks.

### Stage 2: Triplet/Context Expansion
- **Process**: For every anchor chunk found in Stage 1, the system identifies its `book_id` and `chunk_index`. It then performs a secondary metadata query to fetch all chunks in the range: `[chunk_index - 3] TO [chunk_index + 3]`.
- **Reasoning**: In Gaudiya Vaishnava texts, truth is presented in "triplets":
    1. **Sloka** (The Sanskrit/Bengali seed).
    2. **Translation** (The direct meaning).
    3. **Explanation/Purport** (The theological expansion).
- **Outcome**: A single semantic hit expands into a full narrative block, providing the LLM with the complete context needed for a cited answer.

## 2. Output Anatomy
Each "Hit" in the terminal or output file is structured as follows:
- **HIT Header**: Metadata summary (Author, Book Title, Relevance Score).
- **Chunk Labeling**: Every segment is prefixed with its functional type:
    - `[SLOKA]`: The root verse.
    - `[TRANSLATION]`: The direct English rendering.
    - `[EXPLANATION]`: Acharya's commentary.
    - `[PROSE]`: General narrative context.
- **Positional References**: Chapter and verse numbers (e.g., `(8.1)`) are injected into the text stream to assist the LLM with academic-grade citations.

## 3. Density vs. Utility
**Is this too much information?**
From a token-efficiency standpoint, yes. However, from an **Ontological Fidelity** standpoint, it is optimal. By providing the "neighborhood" of a verse, we ensure the LLM understands not just *what* was said, but *why* it was said in the context of the larger discussion (e.g., distinguishing between Brahman realization and pure Bhakti).

## 4. De-duplication
The system uses a `seen_ids` set during the expansion phase. If two semantic hits are from the same chapter, their expanded windows will overlap. The system merges these into a single contiguous block of text to save context space.
