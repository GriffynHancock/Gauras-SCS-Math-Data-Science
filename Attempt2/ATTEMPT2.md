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
    "book_id": "",
    "title": "",
    "author": "Srila B.R. Sridhar Maharaj",
    "chunk_index": 0,
    "type": "prose | song | sloka | discourse | introduction | directory",
    "topics": ["Guru-tattva", "Seva", "History", "Vishnu Tattva"],
    "entities": ["Mahaprabhu", "Nityananda", "Vedas", "Harinam"],
    "has_sloka": True,
    "source_ref": ["SB 5:12", "Harinamamrita Vyakaranam"],
    "summary": ""
  }
}
```

#### Song Metadata Example
For devotional songs, we pair the transliterated verse with its English translation:
```json
{
  "id": "jayare-jayare-jaya-paramahamsa-mahashiaya_v19",
  "verse": "te-kāraṇe prayāsa yathā vāmanera āśa\ngaganera chā̐da dhori bāre\nadoṣa-daraśī tumi adhama patita āmi\nnija guṇe kṣomivā āmāre\n\n",
  "translation": (19) For this reason I endeavour thus, just like a dwarf aspiring to reach the moon. I am lowly and fallen, but your nature is not to consider any offence, so I beg you to pardon my flaws.",
  "metadata": {
    "title": "jayare-jayare-jaya-paramahamsa-mahashiaya",
    "verse_number": 19,
    "author": "Srila Bhaktivinoda Thakur",
    "type": "song"
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

### MCP Server Setup (Jan.ai / Claude)

You can use this RAG pipeline as a tool within Jan.ai or Claude Desktop using the Model Context Protocol (MCP).

### 1. Enable MCP in Jan.ai
- Open Jan.ai -> **Settings** -> **Advanced**.
- Toggle **Experimental Features** to **ON**.
- Go to **Settings** -> **MCP Servers**.
- (Optional but recommended) Toggle **Allow All MCP Tool Permissions** to **ON**.

### 2. Add the Gaudiya RAG Server
Click **Add Server** and use the following configuration:

- **Server Name:** `GaudiyaRAG`
- **Command:** `/Users/gaura/scss/Attempt2/.venv/bin/python`
- **Arguments:** `/Users/gaura/scss/Attempt2/mcp_server.py`

### 3. Claude Desktop Setup
To use this server with Claude Desktop, add the following configuration to your `claude_desktop_config.json` file:

**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

```json
{
  "mcpServers": {
    "GaudiyaRAG": {
      "command": "/Users/gaura/scss/Attempt2/.venv/bin/python",
      "args": [
        "/Users/gaura/scss/Attempt2/mcp_server.py"
      ]
    }
  }
}
```

**Note:** You must restart Claude Desktop after saving this file.

### 4. Usage
Once connected, any model with tool-calling capabilities (e.g., GPT-4o, Claude 3.5, or a local model with tool support) will see the `gaudiya_rag_query` tool. You can ask questions like "Who is Mahaprabhu according to Sridhar Maharaj?" and the model will autonomously use the RAG tool to fetch the answer.

## Directory Structure
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
