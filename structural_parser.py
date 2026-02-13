import re
import json
from pathlib import Path

class StructuralParser:
    def __init__(self):
        # Patterns for verses and chapters
        self.patterns = [
            # (Chapter.Verse) e.g., (8.1)
            re.compile(r'\((\d+)\.(\d+)\)'),
            # [Verse] e.g., [18]
            re.compile(r'\[(\d+)\]'),
            # Verse X
            re.compile(r'Verse\s+(\d+)', re.I),
            # (Book: Chapter.Verse)
            re.compile(r'\(([\u0100-\u017F\w\s-]+):\s*(\d+)\.(\d+)\)')
        ]

    def extract_position(self, text):
        for pattern in self.patterns:
            match = pattern.search(text)
            if match:
                groups = match.groups()
                if len(groups) == 2: # (8.1)
                    return {"chapter": groups[0], "verse": groups[1]}
                elif len(groups) == 1: # [18]
                    return {"verse": groups[0]}
                elif len(groups) == 3: # (Book: 4.34)
                    return {"source_book": groups[0], "chapter": groups[1], "verse": groups[2]}
        return {}

    def refine_metadata(self, chunks):
        print(f"🔍 Refining positional metadata for {len(chunks)} chunks...")
        for chunk in chunks:
            pos = self.extract_position(chunk['text'])
            if pos:
                chunk['metadata'].update(pos)
        return chunks

def main():
    parser = StructuralParser()
    input_file = Path("data/processed/advanced_chunks.json")
    with open(input_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    refined_chunks = parser.refine_metadata(chunks)

    output_file = Path("data/processed/refined_chunks.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(refined_chunks, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Refined chunks saved to {output_file}")

if __name__ == "__main__":
    main()
