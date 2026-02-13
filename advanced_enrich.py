import os
import json
import re
import unicodedata
from pathlib import Path
from unstructured.partition.text import partition_text
from unstructured.chunking.title import chunk_by_title

class StructuralEnricher:
    def __init__(self):
        # Patterns for detecting verses/slokas
        self.verse_marker = re.compile(r'^\s*Verse\s+\d+', re.I)
        self.translation_marker = re.compile(r'^\s*Translation', re.I)
        self.purport_marker = re.compile(r'^\s*Purport', re.I)
        self.bracketed_verse = re.compile(r'\(\d+\)')
        self.citation_pattern = re.compile(r'\([\u0100-\u017F\w\s-]+:\s*\d+\.\d+\)')

    def get_author(self, filename, folder_context=""):
        filename_lower = filename.lower()
        context_lower = folder_context.lower()
        
        if 'sridhar' in filename_lower or 'sridhar' in context_lower:
            return "Srila B.R. Sridhar Maharaj"
        if 'govinda' in filename_lower or 'govinda' in context_lower:
            return "Srila B.S. Govinda Maharaj"
        if 'bhaktivinod' in filename_lower or 'vinod' in context_lower or 'saranagati' in filename_lower:
            return "Srila Bhakti Vinod Thakur"
        if 'mahaprabhu' in filename_lower or 'siddhanta' in context_lower:
            return "Srila Bhakti Siddhanta Saraswati Thakur"
        return "Unknown"

    def is_sloka(self, text):
        # Heuristic: High density of non-ASCII characters (diacritics) often indicates Sanskrit/Bengali transliteration
        diacritics = len(re.findall(r'[\u0100-\u017F]', text))
        if diacritics > 5 and len(text.split()) < 50:
            return True
        if self.verse_marker.search(text) or self.bracketed_verse.search(text):
            return True
        return False

    def process_file(self, file_path, category="book", author_context=""):
        print(f"  📦 Structural Processing: {file_path.name}...")
        elements = partition_text(filename=str(file_path))
        
        chunks = chunk_by_title(
            elements,
            combine_text_under_n_chars=300,
            max_characters=1500,
            new_after_n_chars=1000
        )
        
        book_id = file_path.stem
        author = self.get_author(book_id, author_context)
        
        enriched_chunks = []
        for i, chunk in enumerate(chunks):
            text = chunk.text
            chunk_type = "prose"
            
            if self.is_sloka(text):
                chunk_type = "sloka"
            elif self.translation_marker.search(text):
                chunk_type = "translation"
            elif self.purport_marker.search(text):
                chunk_type = "purport"
            
            # Sub-category for songs
            if category == "song":
                chunk_type = "song_verse"

            enriched_chunks.append({
                "id": f"{book_id}_ch{i:05d}",
                "text": text,
                "metadata": {
                    "book_id": book_id,
                    "title": book_id.replace("en-", "").replace("non-en-", ""),
                    "author": author,
                    "chunk_index": i,
                    "type": chunk_type,
                    "category": category,
                    "source": file_path.name,
                    "tradition": "Gaudiya Vaishnavism"
                }
            })
        return enriched_chunks

def main():
    enricher = StructuralEnricher()
    all_chunks = []

    # 1. Process Cleaned Books
    cleaned_dir = Path("data/cleaned")
    for file_path in cleaned_dir.glob("*.txt"):
        all_chunks.extend(enricher.process_file(file_path, category="book"))

    # 2. Process Gitanjali Songs
    gitanjali_dir = Path("gaudiya_gitanjali")
    for root, dirs, files in os.walk(gitanjali_dir):
        root_path = Path(root)
        for file in files:
            if file.endswith(".txt"):
                file_path = root_path / file
                # Use parent folder name as author context
                all_chunks.extend(enricher.process_file(file_path, category="song", author_context=root_path.name))

    output_file = Path("data/processed/advanced_chunks.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created {len(all_chunks)} advanced chunks in {output_file}")

if __name__ == "__main__":
    main()
