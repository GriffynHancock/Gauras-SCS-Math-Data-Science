# Sri Chaitanya Saraswat Math Expert RAG 2.0

A high-fidelity RAG (Retrieval-Augmented Generation) pipeline for Gaudiya Vaishnava theology, specifically from the Sri Chaitanya Saraswat Math tradition.

## Features
- **Semantic Enrichment**: Automatic entity tagging (Krishna, Mahaprabhu, etc.) and theological topic mapping.
- **Structural Awareness**: Distinguishes between Sloka, Translation, Explanation, Prose, and Songs.
- **Context Expansion**: Retrieves full logical "triplets" (Verse + Translation + Purport).
- **Local LLM**: Integrated with `llama.cpp` using Llama 3.1 8B Instruct for private, offline data processing.
- **Canonical Transliteration**: Automatic generation of IAST diacritics for Sanskrit/Bengali text.

## Architecture
1. **Cleaning**: `canonical_normalize.py` removes OCR noise and institutional boilerplate.
2. **Chunking**: `advanced_enrich_v2.py` creates semantically aware segments.
3. **Enrichment**: `real_llm_enricher.py` uses a local Llama API to add metadata.
4. **Vector DB**: ChromaDB collection `scsmath_advanced` stores embeddings and rich metadata.
5. **Retrieval**: `expert_rag_v2.py` provides an "Expert" CLI for deep theological queries.

## Setup
1. Build `llama.cpp` locally (see `SCSM_RAG_REWRITE_PLAN.md`).
2. Run the `llama-server` with the provided Llama 3.1 GGUF.
3. Ingest data using `rebuild_expert_db.py`.
4. Query using `./.venv311/bin/python expert_rag_v2.py "Your Question"`.

## Project Status
Currently in **Phase 6: Real LLM Enrichment**. 100 sample chunks processed with high-quality semantic tags.

**Jay Srila Guru Maharaj!**
