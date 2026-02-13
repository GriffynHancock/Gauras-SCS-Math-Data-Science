import json
import random
import os
from pathlib import Path

def sample_for_taxonomy(input_file, sample_size=100):
    with open(input_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    sample = random.sample(chunks, min(sample_size, len(chunks)))
    
    # Format for LLM analysis
    formatted_sample = []
    for i, chunk in enumerate(sample):
        # Using a safer way to append multiline strings
        entry = "--- CHUNK " + str(i) + " ---\n" + chunk['text'] + "\n"
        formatted_sample.append(entry)
    
    output_path = Path("data/processed/taxonomy_sample.txt")
    output_path.write_text("\n".join(formatted_sample), encoding='utf-8')
    print(f"📝 Sample for taxonomy generation saved to {output_path}")

if __name__ == "__main__":
    sample_for_taxonomy("data/processed/refined_chunks.json")
