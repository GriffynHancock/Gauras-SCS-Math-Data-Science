import os
import json
import shutil
from pathlib import Path
from ingestion_pipeline import IngestionPipeline

def run_test_run_1():
    # Setup paths relative to script
    script_dir = Path(__file__).parent.absolute()
    output_dir = script_dir / "test_run_1"
    os.makedirs(output_dir / "db", exist_ok=True)
    os.makedirs(output_dir / "processed", exist_ok=True)

    pipeline = IngestionPipeline(
        db_path=str(output_dir / "db"),
        model_dir=str(script_dir / "models")
    )
    
    # Override halted log path for this run
    pipeline.halted_log_path = str(output_dir / "processed" / "halted_chunks.log")
    
    # Define selected files
    library_dir = script_dir / "scsmath_library"
    gitanjali_dir = script_dir / "gaudiya_gitanjali"
    
    selected_books = [
        "en-LovingSearchForTheLostServant.txt",
        "en-HeartandHalo.txt",
        "en-RevealedTruth.txt",
        "en-SubjectiveEvolutionofConsciousness.txt",
        "en-SermonsoftheGuardianofDevotionVol2.txt"
    ]
    
    selected_song_folders = [
        "Compositions_of_Śrīla_Govinda_Mahārāj",
        "Compositions_of_Śrīla_Śrīdhar_Mahārāj",
        "Evening_Songs"
    ]

    # Map the actual folder names if they differ in accents
    actual_folders = os.listdir(gitanjali_dir)
    final_song_folders = []
    for sf in selected_song_folders:
        match = None
        if sf in actual_folders:
            match = sf
        else:
            import unicodedata
            norm_sf = unicodedata.normalize('NFC', sf)
            for af in actual_folders:
                if unicodedata.normalize('NFC', af) == norm_sf:
                    match = af
                    break
        if match:
            final_song_folders.append(match)
        else:
            print(f"⚠️ Could not find song folder: {sf}")

    print("🚀 Stage 1: Ingesting selected files...")
    
    all_chunks = []
    from tools.scripture_chunker import ScriptureChunker
    
    # Ingest Books
    for book in selected_books:
        book_path = library_dir / book
        if book_path.exists():
            print(f"Ingesting book: {book}")
            with open(book_path, 'r', encoding='utf-8') as f:
                text = f.read()
            book_id = book_path.stem
            normal_chunks = ScriptureChunker.split_into_normal_chunks(text)
            for i, nc in enumerate(normal_chunks):
                chunk_id = f"{book_id}_chunk_{i}"
                metadata = {
                    "book_id": book_id, 
                    "title": book_id.replace("en-", ""),
                    "chunk_index": i,
                    "type": "prose"
                }
                all_chunks.append(pipeline._create_gold_standard_chunk(chunk_id, nc, metadata))
        else:
            print(f"⚠️ Book not found: {book_path}")

    # Ingest Songs
    from tools.song_chunker import SongChunker
    song_chunker = SongChunker()
    for folder in final_song_folders:
        folder_path = gitanjali_dir / folder
        print(f"Ingesting song folder: {folder}")
        for song_file in folder_path.glob("*.txt"):
            sc_list = song_chunker.chunk_song(str(song_file))
            for sc in sc_list:
                metadata = {
                    "type": "song",
                    "title": sc['metadata'].get('title'),
                    "author": sc['metadata'].get('author'),
                    "chunk_index": sc['metadata'].get('verse_number', 0),
                    "has_sloka": True,
                    "first_line_sloka": ScriptureChunker.get_first_transliterated_line(sc['text'])
                }
                all_chunks.append(pipeline._create_gold_standard_chunk(sc['id'], sc['text'], metadata))

    print(f"Total raw chunks: {len(all_chunks)}")

    # Save raw chunks
    raw_chunks_file = output_dir / "processed" / "raw_chunks.jsonl"
    with open(raw_chunks_file, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    
    print(f"\n🧠 Stage 2: Enriching {len(all_chunks)} chunks...")
    state_file = output_dir / "processed" / "enrichment_state.json"
    checkpoint_file = output_dir / "processed" / "enriched_chunks.jsonl"
    
    enriched_chunks = []
    if os.path.exists(checkpoint_file):
        print(f"Resuming from {checkpoint_file}")
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            for line in f:
                enriched_chunks.append(json.loads(line))
    
    start_idx = len(enriched_chunks)
    if start_idx < len(all_chunks):
        pipeline.load_llm()
        try:
            for i in range(start_idx, len(all_chunks)):
                chunk = all_chunks[i]
                print(f"[{i+1}/{len(all_chunks)}] Enriching {chunk['id']}...")
                enriched = pipeline._enrich_single_chunk(chunk)
                enriched_chunks.append(enriched)
                with open(checkpoint_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(enriched, ensure_ascii=False) + '\n')
                if (i + 1) % 10 == 0:
                    with open(state_file, 'w') as f:
                        json.dump({'last_completed_index': i}, f)
        finally:
            pipeline.unload_llm()
    else:
        print("All chunks already enriched.")

    print(f"\n📂 Stage 3: Indexing {len(enriched_chunks)} chunks...")
    chunks_to_index = enriched_chunks

    try:
        # Clear existing collection if any
        try:
            pipeline.client.delete_collection("test_run_1_collection")
        except:
            pass
        
        pipeline.build_index(chunks_to_index, collection_name="test_run_1_collection")
        print(f"✅ Pipeline complete! Indexed {len(chunks_to_index)} chunks.")
    except Exception as e:
        print(f"\n❌ Indexing failed: {e}")

if __name__ == "__main__":
    run_test_run_1()
