import os
import json
from ingestion_pipeline import IngestionPipeline

def run_ingestion():
    pipeline = IngestionPipeline(
        db_path="data/test_db",
        model_dir="models"
    )
    
    # Remove state file to force a fresh run for 2 chunks
    state_file = "data/processed/enrichment_state.json"
    checkpoint_file = "data/processed/enriched_chunks.jsonl"
    if os.path.exists(state_file):
        os.remove(state_file)
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)
    if os.path.exists(pipeline.halted_log_path): # Clear halted log too
        os.remove(pipeline.halted_log_path)


    print("🚀 Stage 1: Ingesting...")
    song_chunks = pipeline.ingest_songs("data/micro_test/songs")
    book_chunks = pipeline.ingest_books("data/micro_test/books")
    all_chunks = song_chunks + book_chunks
    print(f"Total raw chunks: {len(all_chunks)}")

    # Save raw chunks for backup
    os.makedirs("data/processed", exist_ok=True)
    with open("data/processed/raw_chunks.jsonl", "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    
    # --- Processing only 2 chunks for review ---
    chunks_to_enrich = all_chunks[:2]
    print(f"\n🧠 Stage 2: Enriching {len(chunks_to_enrich)} chunks (limited for review)...")
    
    enriched_chunks = pipeline.enrich_chunks(chunks_to_enrich, batch_size=1) # batch_size 1 for closer observation
    # --- End of limited processing ---
    
    print(f"\n📂 Stage 3: Indexing {len(enriched_chunks)} chunks...")
    # The build_index method now handles model loading robustly
    try:
        pipeline.build_index(enriched_chunks, collection_name="test_collection")
        print("✅ Pipeline complete!")
    except Exception as e:
        print(f"\n❌ Indexing failed: {e}")
        print("Enriched chunks saved to JSONL but indexing skipped.")

if __name__ == "__main__":
    run_ingestion()
