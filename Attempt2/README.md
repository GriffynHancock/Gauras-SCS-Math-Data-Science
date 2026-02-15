# Attempt 2: Streamlined Expert RAG Pipeline

This directory contains the second iteration of the Gaudiya Vaishnava RAG pipeline, focused on structural consistency, resource efficiency, and high-fidelity scripture processing.

## Key Components

### 1. Ingestion & Chunking
- **`ingestion_pipeline.py`**: The core ingestion engine.
- **`tools/scripture_chunker.py`**: Specialized logic for parsing scriptures (Bhagavad-gita, Brahma Samhita, etc.). It ensures Verse-Transliteration-Translation are kept as atomic units.
- **`test_ingestion.py`**: Driver script for bulk processing with resume capability.

### 2. Enrichment
- **NOTE: The `bert-large-NER` model is currently non-functional and has been disabled.**
- **LLM-Driven Tagging**: Uses `Jan-v3-4b` (via llama.cpp) for deep theological tagging, including topics, entities, and summaries.
- **Resume-Safe**: Progress is checkpointed to `enriched_chunks.jsonl`, allowing the process to survive crashes or interruptions.
- **Prompt Driven**: Driven by `PROMPT.txt`, enforcing strict metadata extraction rules (topics, entities, summaries).

### 3. RAG & Retrieval
- **`rag_pipeline.py`**: Handles semantic search and answer synthesis.
- **Answer Synthesis**: Uses the Jan model to generate theological responses based on retrieved context.
- **Gold Standard Schema**: All data adheres to the canonical schema defined in `ATTEMPT2.md`.

## Data Structure (The "Gold Standard")
Every chunk contains:
- `text`: Unified content (Verse + Translit + Trans).
- `metadata`:
    - `topics`: Thematic labels (e.g., Guru-tattva).
    - `entities`: Mentioned people/deities.
    - `summary`: 2-sentence theological gist.
    - `first_line_sloka`: Transliterated anchor for contextual linkage.
    - `type`:song, shastra, or null (for prose).

## Quick Start

1. **Setup Environment**:
   ```bash
   cd Attempt2
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run Bulk Ingestion & Enrichment**:
   ```bash
   python test_ingestion.py
   ```

3. **Query the RAG Pipeline**:
   ```bash
   python test_rag.py
   ```

## MCP Integration (Jan.ai / Claude)

This pipeline can be exposed as a **Model Context Protocol (MCP)** server, allowing AI agents like Jan.ai or Claude Desktop to query the Gaudiya Vaishnava scriptures as a tool.

### Setup in Jan.ai:
1. Enable **Experimental Features** in Settings.
2. Add a new **MCP Server**:
   - **Command**: `/Users/gaura/scss/Attempt2/.venv/bin/python`
   - **Arguments**: `/Users/gaura/scss/Attempt2/mcp_server.py`

### Setup in Claude Desktop:
Add the server configuration to your `claude_desktop_config.json`. See `ATTEMPT2.md` for the full JSON snippet and file location.

## Requirements
- `fastmcp`
- `llama-index`
- `chromadb`
- `sentence-transformers`
- `llama-cpp-python`
- `transformers`
- `torch`
