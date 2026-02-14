import os
import json
import re
import random
from pathlib import Path

class SongChunker:
    def __init__(self):
        # Pattern to find verse markers like (1), (2), etc.
        self.verse_num_pattern = re.compile(r'^\s*\((\d+)\)\s*(.*)', re.DOTALL)

    def process_song_file(self, file_path, author="Unknown"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []

        if not lines: return []

        # Extract title (usually first few lines)
        title = file_path.stem.replace("-", " ").title()
        # Heuristic: First non-empty line is often the title if not in filename
        for line in lines[:5]:
            if line.strip():
                # If line is short and looks like a title
                if len(line.strip()) < 100:
                    title = line.strip()
                break

        content = "".join(lines)
        # Split by verse numbers like (1), (2)
        parts = re.split(r'\s*\((\d+)\)\s*', content)
        
        chunks = []
        if len(parts) < 3: 
            # If no verse numbers found, treat whole file as one chunk or split by paragraphs
            # For songs, usually verses are numbered. If not, maybe it's a short song.
            chunks.append({
                "id": f"{file_path.stem}_whole",
                "text": content.strip(),
                "metadata": {
                    "book_id": file_path.stem,
                    "title": title,
                    "author": author,
                    "verse_number": 0,
                    "type": "song",
                    "category": "song",
                    "source": file_path.name,
                    "is_lila": True,
                    "has_sloka": True # Songs usually have slokas/verses
                }
            })
            return chunks
        
        preamble = parts[0].strip()
        
        # Preamble might contain the first verse if it wasn't numbered (1)
        # But usually (1) starts the first verse.
        # Sometimes preamble has the refrain (Refrain) or (Tek)
        
        # We will iterate through parts: [preamble, '1', 'text for 1', '2', 'text for 2', ...]
        
        current_verse_num = 0
        
        for i in range(1, len(parts), 2):
            verse_num_str = parts[i]
            try:
                verse_num = int(verse_num_str)
            except ValueError:
                verse_num = 0
            
            verse_text = parts[i+1].strip()
            
            # Check for translation vs original
            # Often structured as:
            # Original Bengali/Sanskrit
            # 
            # Translation
            
            full_chunk_text = f"({verse_num})\n{verse_text}"
            
            chunks.append({
                "id": f"{file_path.stem}_v{verse_num}",
                "text": full_chunk_text,
                "metadata": {
                    "book_id": file_path.stem,
                    "title": title,
                    "author": author,
                    "verse_number": verse_num,
                    "type": "song",
                    "category": "song",
                    "source": file_path.name,
                    "is_lila": True,
                    "has_sloka": True
                }
            })

        return chunks

def main():
    chunker = SongChunker()
    all_chunks = []
    
    gitanjali_dir = Path("gaudiya_gitanjali")
    processed_dir = Path("data/micro_test/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Authors mapping based on folder names
    authors_map = {
        "Compositions_of_Śrīla_Śrīdhar_Mahārāj": "Srila B.R. Sridhar Maharaj",
        "Compositions_of_Śrīla_Govinda_Mahārāj": "Srila B.S. Govinda Maharaj",
        "Songs_of_Śrīla_Bhaktivinoda_Ṭhākura": "Srila Bhakti Vinod Thakur",
        "Songs_to_Śrī_Chaitanya_Mahāprabhu": "Various",
        "Songs_to_Śrī_Krishna": "Various",
        "Songs_to_Śrīmatī_Rādhārāṇī": "Various"
    }

    print("🎵 Scanning for songs...")
    all_song_files = []
    
    # Recursively find all .txt files
    for root, dirs, files in os.walk(gitanjali_dir):
        for file in files:
            if file.endswith(".txt"):
                # Check exclusion list
                if "Premadhama" in file or "premadhama" in file:
                    continue
                if "Siksastakam" in file: # Optional exclusion if too long
                    continue
                
                full_path = Path(root) / file
                
                # Determine author
                author = "Unknown"
                for folder_key, author_name in authors_map.items():
                    if folder_key in str(full_path):
                        author = author_name
                        break
                
                all_song_files.append((full_path, author))

    print(f"Found {len(all_song_files)} candidate songs.")
    
    # Randomly select 10
    if len(all_song_files) > 10:
        selected_songs = random.sample(all_song_files, 10)
    else:
        selected_songs = all_song_files
        
    print(f"Selecting {len(selected_songs)} songs:")
    for song_path, author in selected_songs:
        print(f"  - {song_path.name} ({author})")
        new_chunks = chunker.process_song_file(song_path, author=author)
        all_chunks.extend(new_chunks)
        print(f"    -> {len(new_chunks)} verses")

    output_file = processed_dir / "song_chunks.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    print(f"🎉 Created {len(all_chunks)} song chunks from {len(selected_songs)} files.")

if __name__ == "__main__":
    main()
