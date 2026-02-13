import os
import json
import re
from pathlib import Path
from unstructured.partition.text import partition_text
from unstructured.chunking.title import chunk_by_title

class RobustStructuralEnricher:
    def __init__(self):
        # Markers
        self.verse_marker = re.compile(r'^\s*Verse\s+\d+', re.I)
        self.translation_marker = re.compile(r'^\s*Translation', re.I)
        self.purport_marker = re.compile(r'^\s*Purport', re.I)
        self.ref_marker = re.compile(r'\(.*?\d+[\.:]\d+.*?\)|\[\d+\]')
        
        # Script ranges
        self.sanskrit_range = re.compile(r'[\u0900-\u097F]')
        self.bengali_range = re.compile(r'[\u0980-\u09FF]')
        self.diacritic_range = re.compile(r'[\u0100-\u017F]')

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

    def determine_type(self, text, prev_type=None, is_song=False):
        if is_song:
            return "song_verse"
            
        # 1. Check for explicit markers
        if self.verse_marker.search(text):
            return "sloka"
        if self.translation_marker.search(text):
            return "translation"
        if self.purport_marker.search(text):
            return "explanation"
            
        # 2. Check for script-heavy blocks (Slokas)
        sanskrit_chars = len(self.sanskrit_range.findall(text))
        bengali_chars = len(self.bengali_range.findall(text))
        diacritic_chars = len(self.diacritic_range.findall(text))
        
        # If it has significant Sanskrit/Bengali script, it's definitely a sloka
        if sanskrit_chars > 10 or bengali_chars > 10:
            return "sloka"
            
        # If it has high diacritic density relative to length, it's likely a sloka or transliteration
        if diacritic_chars > 15 and len(text.split()) < 100:
            return "sloka"
            
        # 3. Contextual flow
        if prev_type == "sloka":
            # If it follows a sloka and doesn't look like a new sloka, it's a translation
            return "translation"
        
        if prev_type == "translation":
            # If it follows a translation, it's an explanation
            return "explanation"
            
        if prev_type == "explanation" and len(text.split()) > 50:
            # Continue explanation type for contiguous commentary
            return "explanation"
            
        # 4. Keyword heuristic for explanations
        explanation_keywords = ['Mahārāj', 'Mahāprabhu', 'Kṛṣṇa', 'verse', 'explains', 'commentary']
        if any(kw in text for kw in explanation_keywords) and len(text.split()) > 30:
            return "explanation"

        return "prose"

    def process_file(self, file_path, category="book", author_context=""):
        elements = partition_text(filename=str(file_path))
        chunks = chunk_by_title(
            elements,
            combine_text_under_n_chars=400,
            max_characters=1500,
            new_after_n_chars=1000
        )
        
        book_id = file_path.stem
        author = self.get_author(book_id, author_context)
        
        enriched_chunks = []
        last_type = None
        
        for i, chunk in enumerate(chunks):
            current_type = self.determine_type(chunk.text, prev_type=last_type, is_song=(category=="song"))
            
            # Refine Sloka: if it also has a citation and English text, it's a primary scriptural unit
            if current_type == "sloka" and self.ref_marker.search(chunk.text) and len(chunk.text.split()) > 40:
                # Keep as sloka but it's a 'dense' one
                pass

            enriched_chunks.append({
                "id": f"{book_id}_ch{i:05d}",
                "text": chunk.text,
                "metadata": {
                    "book_id": book_id,
                    "title": book_id.replace("en-", "").replace("non-en-", ""),
                    "author": author,
                    "chunk_index": i,
                    "type": current_type,
                    "category": category,
                    "source": file_path.name,
                    "tradition": "Gaudiya Vaishnavism"
                }
            })
            last_type = current_type
            
        return enriched_chunks

def main():
    enricher = RobustStructuralEnricher()
    all_chunks = []

    # Process Books
    cleaned_dir = Path("data/cleaned")
    for file_path in sorted(cleaned_dir.glob("*.txt")):
        all_chunks.extend(enricher.process_file(file_path, category="book"))

    # Process Songs
    gitanjali_dir = Path("gaudiya_gitanjali")
    for root, dirs, files in os.walk(gitanjali_dir):
        root_path = Path(root)
        for file in sorted(files):
            if file.endswith(".txt"):
                all_chunks.extend(enricher.process_file(root_path / file, category="song", author_context=root_path.name))

    output_file = Path("data/processed/robust_chunks.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Created {len(all_chunks)} robustly typed chunks in {output_file}")

if __name__ == "__main__":
    main()
