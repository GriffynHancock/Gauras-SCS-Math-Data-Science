import json
from pathlib import Path
from structural_parser import StructuralParser

def main():
    parser = StructuralParser()
    input_file = Path("data/processed/granular_chunks.json")
    with open(input_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    print(f"🔍 Refining positional metadata for {len(chunks)} granular chunks...")
    refined_chunks = parser.refine_metadata(chunks)

    output_file = Path("data/processed/refined_granular_chunks.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(refined_chunks, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Positional refinement complete: {output_file}")

if __name__ == "__main__":
    main()
