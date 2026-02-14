import os
import json
import re
from pathlib import Path
from unstructured.partition.text import partition_text
from unstructured.chunking.title import chunk_by_title

class MicroDatasetChunker:
    def __init__(self):
        # Markers
        self.verse_marker = re.compile(r'^\s*Verse\s+\d+', re.I)
        self.translation_marker = re.compile(r'^\s*Translation', re.I)
        self.purport_marker = re.compile(r'^\s*Purport', re.I)
        
    def get_author(self, filename):
        filename_lower = filename.lower()
        if 'sridhar' in filename_lower:
            return "Srila B.R. Sridhar Maharaj"
        if 'govinda' in filename_lower:
            return "Srila B.S. Govinda Maharaj"
        if 'bhaktivinod' in filename_lower or 'saranagati' in filename_lower:
            return "Srila Bhakti Vinod Thakur"
        if 'mahaprabhu' in filename_lower:
            return "Srila Bhakti Siddhanta Saraswati Thakur"
        return "Unknown"

    def determine_type(self, text, prev_type=None):
        if self.verse_marker.search(text):
            return "sloka"
        if self.translation_marker.search(text):
            return "translation"
        if self.purport_marker.search(text):
            return "explanation"
            
        # Heuristic for detecting a sloka block (dense diacritics or bracketed numbers)
        diacritics = len(re.findall(r'[\u0100-\u017F]', text))
        if diacritics > 10 and len(text.split()) < 40:
            return "sloka"
            
        return "prose"

    def process_file(self, file_path):
        # Read text manually first to avoid unstructured encoding issues if any
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []

        # We can pass the text directly to partition_text if we want, but filename is usually fine.
        # However, since these are snippets, let's just use partition_text on the file.
        elements = partition_text(filename=str(file_path))
        
        # Chunking strategy
        chunks = chunk_by_title(
            elements,
            combine_text_under_n_chars=300,
            max_characters=1500,
            new_after_n_chars=1000
        )
        
        book_id = file_path.stem
        author = self.get_author(book_id)
        
        enriched_chunks = []
        last_type = None
        
        for i, chunk in enumerate(chunks):
            current_type = self.determine_type(chunk.text, prev_type=last_type)
            
            # remove the "--- EXTRACTED FROM ..." header if it got chunked alone or at start
            clean_text = chunk.text
            if "--- EXTRACTED FROM" in clean_text:
                clean_text = clean_text.split("---")[-1].strip()
            
            if not clean_text:
                continue

            enriched_chunks.append({
                "id": f"{book_id}_micro_{i:03d}",
                "text": clean_text,
                "metadata": {
                    "book_id": book_id,
                    "title": book_id.replace("en-", "").replace("non-en-", ""),
                    "author": author,
                    "chunk_index": i,
                    "type": current_type,
                    "category": "micro_test",
                    "source": file_path.name,
                    "tradition": "Gaudiya Vaishnavism"
                }
            })
            last_type = current_type
            
        return enriched_chunks

def main():
    chunker = MicroDatasetChunker()
    all_chunks = []

    raw_dir = Path("data/micro_test/raw")
    processed_dir = Path("data/micro_test/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    print(f"🧩 Chunking files in {raw_dir}...")
    for file_path in raw_dir.glob("*.txt"):
        new_chunks = chunker.process_file(file_path)
        all_chunks.extend(new_chunks)
        # print(f"  Processed {file_path.name} -> {len(new_chunks)} chunks")

    output_file = processed_dir / "chunks.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created {len(all_chunks)} chunks in {output_file}")

if __name__ == "__main__":
    main()
