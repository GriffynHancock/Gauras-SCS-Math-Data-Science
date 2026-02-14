import json
from pathlib import Path
from langdetect import detect, DetectorFactory
import re

# For reproducibility in language detection
DetectorFactory.seed = 0

def clean_text(text):
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def prepare_canonical():
    input_file = Path("data/processed/refined_robust_chunks.json")
    output_file = Path("data/processed/canonical_chunks.jsonl")

    if not input_file.exists():
        print(f"❌ Input file {input_file} not found.")
        return

    print(f"📖 Loading chunks from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    print(f"🛠 Processing {len(chunks)} chunks into canonical format...")
    
    with open(output_file, 'w', encoding='utf-8') as f_out:
        for chunk in chunks:
            # Step 1.1 & 1.2
            canonical_chunk = {
                "chunk_id": chunk["id"],
                "doc_id": chunk["metadata"].get("book_id", "unknown"),
                "chunk_text": clean_text(chunk["text"]),
                "chunk_text_raw": chunk["text"],
                "structural_path": {
                    "book": chunk["metadata"].get("title"),
                    "chapter": chunk["metadata"].get("chapter"),
                    "verse": chunk["metadata"].get("verse")
                },
                "metadata": chunk["metadata"] # Keep original metadata too
            }
            
            # Detect language
            try:
                # Use a snippet for faster detection if text is long
                detection_text = canonical_chunk["chunk_text"][:500]
                lang = detect(detection_text)
                canonical_chunk["language"] = lang
            except:
                canonical_chunk["language"] = "unknown"
                
            # Coarse category label (Step 3.4 preview)
            canonical_chunk["chunk_type"] = chunk["metadata"].get("type", "prose")

            f_out.write(json.dumps(canonical_chunk, ensure_ascii=False) + "\n")

    print(f"✅ Canonical dataset saved to {output_file}")

if __name__ == "__main__":
    prepare_canonical()
