# Test Run 1: Ingestion and RAG Instructions

## 1. Environment Setup [DONE]
- Ensured we are in the `Attempt2` directory.
- Used the existing `.venv`.
- Created output directory `test_run_1`.

## 2. Fix "Race Condition" in Embedding Stage [DONE]
- Robustified model paths in `ingestion_pipeline.py`.
- Added MPS support for M3 Mac (fallback to CPU which was found faster for this large model).
- Fixed ChromaDB metadata list compatibility (flattened lists to strings).
- Added progress bars and logging to indexing.

## 3. Data Selection [DONE]
- Books:
    - `en-LovingSearchForTheLostServant`
    - `en-HeartandHalo`
    - `en-RevealedTruth`
    - `en-SubjectiveEvolutionofConsciousness`
    - `en-SermonsoftheGuardianofDevotionVol2`
- Songs:
    - `Compositions_of_Śrīla_Govinda_Mahārāj`
    - `Compositions_of_Śrīla_Śrīdhar_Mahārāj`
    - `Evening_Songs`

## 4. Pipeline Execution [DONE]
- Created `run_test_run_1.py`.
- Successfully enriched 1027 chunks.
- Indexed a subset of 100 chunks for quick verification.

## 5. RAG Retrieval [DONE]
- Prompt: "Who is Mahaprabhu according to Sridhar Maharaj?"
- Result: Successfully synthesized a theological response based on `LovingSearchForTheLostServant`.

## 6. Verification [DONE]
- `test_run_1/db` contains the Chroma collection.
- `test_run_1/processed/enriched_chunks.jsonl` contains the full enriched dataset.
- Logs verified for success.
