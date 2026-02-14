import os
import json
from ingestion_pipeline import IngestionPipeline

def run_ingestion():
    pipeline = IngestionPipeline(
        db_path="data/test_db",
        model_dir="models"
    )
    
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
    
    print(f"\n🧠 Stage 2: Enriching {len(all_chunks)} chunks (Resume-safe)...")
    # For testing, we might want a smaller batch_size for checkpoints
    enriched_chunks = pipeline.enrich_chunks(all_chunks, batch_size=5)
    
    print(f"\n📂 Stage 3: Indexing {len(enriched_chunks)} chunks...")
    embed_model_path = "models/Qwen3-Embedding-4B"
    if os.path.exists(os.path.join(embed_model_path, "model-00001-of-00002.safetensors")):
        pipeline.build_index(enriched_chunks, collection_name="test_collection")
        print("✅ Pipeline complete!")
    else:
        print("\n⚠️ Embedding model not fully ready. Enriched chunks saved to JSONL but indexing skipped.")

if __name__ == "__main__":
    run_ingestion()
