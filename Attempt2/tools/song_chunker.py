import re
import json
import os
from typing import List, Dict, Optional

class SongChunker:
    def __init__(self):
        # Regex to identify verse numbers like (1), (2), etc.
        self.verse_pattern = re.compile(r'^\((\d+)\)\s*(.*)', re.MULTILINE)

    def chunk_song(self, file_path: str, metadata_ext: Dict = None) -> List[Dict]:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')
        title = ""
        author = "Unknown"
        
        # Try to extract title from first line if it looks like a title
        if lines and lines[0].strip() and not lines[0].startswith('('):
            title = lines[0].strip()

        # Simple heuristic for author if mentioned in the text
        if "Bhaktivinoda" in content:
            author = "Srila Bhaktivinoda Thakur"
        elif "Sridhar" in content:
            author = "Srila B.R. Sridhar Maharaj"
        elif "Govinda" in content:
            author = "Srila B.S. Govinda Maharaj"

        # Split content into verses and translations
        chunks = []
        matches = list(self.verse_pattern.finditer(content))
        
        last_pos = 0
        for i, match in enumerate(matches):
            verse_num = int(match.group(1))
            translation = match.group(2).strip()
            
            # The transliteration is between the previous match (or start) and this match
            transliteration_part = content[last_pos:match.start()].strip()
            
            # Clean up transliteration: remove title/header if it's the first verse
            if i == 0 and title in transliteration_part:
                # Remove the title and any potential divider
                transliteration_part = transliteration_part.replace(title, "").strip()
                transliteration_part = re.sub(r'^-+$', '', transliteration_part, flags=re.MULTILINE).strip()

            combined_text = f"{transliteration_part}\n\n({verse_num}) {translation}"
            
            chunk = {
                "id": f"{os.path.basename(file_path).replace('.txt', '')}_v{verse_num}",
                "text": combined_text,
                "metadata": {
                    "title": title,
                    "verse_number": verse_num,
                    "author": author,
                    "type": "song_verse"
                }
            }
            if metadata_ext:
                chunk["metadata"].update(metadata_ext)
                
            chunks.append(chunk)
            last_pos = match.end()

        return chunks

if __name__ == "__main__":
    import sys
    chunker = SongChunker()
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.exists(path):
            chunks = chunker.chunk_song(path)
            print(json.dumps(chunks[0], indent=2, ensure_ascii=False))
