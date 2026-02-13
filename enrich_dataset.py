import os
import json
from pathlib import Path
from unstructured.partition.text import partition_text
from unstructured.chunking.title import chunk_by_title

def get_author(filename):
    """Simple heuristic for author attribution."""
    filename_lower = filename.lower()
    if any(x in filename_lower for x in ['sridhar', 'sguru', 'guardian', 'search']):
        return "Srila B.R. Sridhar Maharaj"
    elif any(x in filename_lower for x in ['govinda', 'sgov', 'affectionate', 'guidance']):
        return "Srila B.S. Govinda Maharaj"
    elif any(x in filename_lower for x in ['bhaktivinod', 'saranagati', 'prema-vivarta']):
        return "Srila Bhakti Vinod Thakur"
    elif 'mahaprabhu' in filename_lower:
        return "Srila Bhakti Siddhanta Saraswati Thakur"
    return "Unknown"

def enrich_and_chunk(input_dir, output_dir):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    files = list(input_path.glob("*.txt"))
    print(f"🧩 Chunking and enriching {len(files)} files.")

    all_chunks = []

    for file_path in files:
        print(f"  📦 Processing {file_path.name}...")
        try:
            # 1. Partition
            elements = partition_text(filename=str(file_path))
            
            # 2. Chunk
            chunks = chunk_by_title(
                elements,
                combine_text_under_n_chars=500,
                max_characters=1500,
                new_after_n_chars=1000
            )
            
            book_id = file_path.stem
            author = get_author(book_id)
            
            for i, chunk in enumerate(chunks):
                chunk_dict = {
                    "id": f"{book_id}_chunk_{i:04d}",
                    "text": chunk.text,
                    "metadata": {
                        "book_id": book_id,
                        "title": book_id.replace("en-", "").replace("non-en-", ""),
                        "author": author,
                        "chunk_index": i,
                        "source": file_path.name,
                        "tradition": "Gaudiya Vaishnavism",
                        "language": "bn" if "non-en" in book_id else "en"
                    }
                }
                all_chunks.append(chunk_dict)
                
        except Exception as e:
            print(f"  ❌ Error processing {file_path.name}: {e}")

    # Save as a large JSON for ingestion or individual files
    output_file = output_path / "enriched_chunks.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created {len(all_chunks)} enriched chunks in {output_file}")

if __name__ == "__main__":
    enrich_and_chunk("data/cleaned", "data/processed")
