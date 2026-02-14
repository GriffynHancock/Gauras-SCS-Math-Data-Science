# Attempt 2: Streamlined Expert RAG Pipeline

## Overview
This phase ("Attempt 2") aims to rebuild the Gaudiya Vaishnava RAG pipeline with a unified, streamlined architecture. We are moving away from ad-hoc scripts to a structured pipeline using state-of-the-art open-source models (Qwen/DeepSeek).

## Goals
1.  **Unified Pipeline:** Single entry point for ingestion, enrichment, and indexing.
2.  **Resource Management:** Ensure only one heavy model (LLM/Embedding) is loaded at a time.
3.  **Data Consistency:** Implement a "Gold Standard" canonical data structure for all chunks.
4.  **High-Fidelity Retrieval:** Use Hybrid Search (BM25 + Semantic) with Qwen-based embeddings and reranking.

## Architecture

### 1. Data Structure (The "Gold Standard")
Every chunk will strictly adhere to this schema:
```json
{
  "id": "unique_id_v1",
  "text": "The actual text content...",
  "metadata": {
    "book_id": "en-RevealedTruth",
    "title": "Revealed Truth",
    "author": "Srila B.R. Sridhar Maharaj",
    "chunk_index": 0,
    "type": "prose | song_verse | sloka | purport",
    "verse_number": 1,
    "topics": ["Guru-tattva", "Seva"],
    "entities": ["Mahaprabhu", "Nityananda"],
    "sentiment": "devotional_ecstasy",
    "source_ref": "Chapter 5, Verse 12"
  }
}
```

#### Song Metadata Example
For devotional songs, we pair the transliterated verse with its English translation:
```json
{
  "id": "gaura-arati_v1",
  "text": "(kiba) jaya jaya gaurāchā̐der ārotiko śobhā\njāhṇavī-taṭa-vane jagamana-lobhā\n(jaga janer mana-lobhā)\n(gaurāṅger āroti śobhā jaga janer mana-lobhā)\n(nitāi gaura haribol)\n\n(1) All glories, all glories to the beautiful ceremony of worship to Lord Gaurachandra in a grove on the banks of the Jāhṇavī river! It is attracting the minds of all living entities in the universe.",
  "metadata": {
    "title": "Śrī Gaura-ārati",
    "verse_number": 1,
    "author": "Srila Bhaktivinoda Thakur",
    "type": "song_verse"
  }
}
```

### 2. Models
*   **LLM (Inference):** `unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF`
    *   File: `DeepSeek-R1-0528-Qwen3-8B-UD-Q6_K_XL.gguf`
*   **Embedding:** `Qwen/Qwen3-Embedding-4B`
*   **Reranker:** `Qwen/Qwen3-Reranker-4B`

### 3. Pipeline Stages
1.  **Ingestion:**
    *   **Books:** `Unstructured` for PDF/Epub/Text parsing.
    *   **Songs:** Custom `SongChunker` (preserves verse/purport structure).
2.  **Enrichment:**
    *   **NER:** `bert-large-NER` for initial entity pass.
    *   **Deep Tagging:** LlamaIndex + DeepSeek for "Theological" tagging (Is this Lila? Who is speaking?).
3.  **Indexing:**
    *   **Vector Store:** ChromaDB (Persistent).
    *   **Search:** Hybrid (BM25 + Cosine Similarity).

## Setup Instructions

### Environment
```bash
cd Attempt2
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Directory Structure
```
Attempt2/
├── .venv/
├── gaudiya_gitanjali/    # Songs source
├── scsmath_library/      # Books source (raw text)
├── tools/                # Utility scripts (migrated)
├── data/
│   ├── raw/
│   ├── processed/
│   └── db/               # ChromaDB
├── models/               # GGUF models
└── ATTEMPT2.md           # This file
```

## Next Steps
1.  **Install Dependencies:** `llama-index`, `chromadb`, `sentence-transformers`, `unstructured`, `torch`.
2.  **Download Models:** Fetch the specific GGUF and embedding models.
3.  **Refactor Tools:** Merge `enrich_*.py` scripts into a `pipeline.py` module.
