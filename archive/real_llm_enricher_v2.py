import json
import requests
import os
from pathlib import Path
from tqdm import tqdm
from collections import defaultdict

class SequentialTheologicalEnricher:
    def __init__(self, api_url="http://127.0.0.1:8080/v1/chat/completions"):
        self.api_url = api_url
        self.system_prompt = Path("system_prompt.txt").read_text(encoding='utf-8')

    def enrich_chunk(self, current_text, prev_text=None):
        context_str = "PREVIOUS CHUNK:\n" + str(prev_text) + "\n\n" if prev_text else "PREVIOUS CHUNK: (None - Start of Book)\n\n"
        
        user_prompt = context_str + "CURRENT CHUNK TO ANALYZE:\n" + current_text + "\n\nAnalyze the CURRENT CHUNK and return JSON metadata."

        payload = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1
        }

        try:
            response = requests.post(self.api_url, json=payload, timeout=120)
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            if content.startswith("```json"): content = content[7:-3].strip()
            elif content.startswith("```"): content = content[3:-3].strip()
                
            return json.loads(content)
        except Exception:
            return None

def main():
    enricher = SequentialTheologicalEnricher()
    input_file = Path("data/processed/refined_granular_chunks.json")
    output_file = Path("data/processed/expert_enriched_chunks.jsonl")

    with open(input_file, 'r', encoding='utf-8') as f:
        all_chunks = json.load(f)

    books = defaultdict(list)
    for c in all_chunks:
        books[c['metadata']['book_id']].append(c)

    processed_ids = set()
    if output_file.exists():
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    c = json.loads(line)
                    processed_ids.add(c['id'])
                except: pass

    print(f"🌟 Starting Batch 2 (Chunks 100-200) with Ontological Rules...")
    
    count = 0
    limit = 100 
    sorted_book_ids = sorted(books.keys())
    
    for book_id in sorted_book_ids:
        book_chunks = books[book_id]
        prev_text = None
        
        for chunk in book_chunks:
            # Check if this chunk is already processed
            already_processed = chunk['id'] in processed_ids
            
            if already_processed:
                prev_text = chunk['text']
                continue
            
            if count >= limit: break
            
            enriched_data = enricher.enrich_chunk(chunk['text'], prev_text)
            if enriched_data:
                chunk['metadata'].update(enriched_data)
                chunk['metadata'].pop('text_canonical', None)
            
            with open(output_file, 'a', encoding='utf-8') as f_out:
                f_out.write(json.dumps(chunk, ensure_ascii=False) + "\n")
            
            prev_text = chunk['text']
            count += 1
            if count % 10 == 0:
                print(f"  ✅ [{count}/{limit}] Enriched: {chunk['id']}")

        if count >= limit: break

    print(f"✅ Batch 2 complete. Results appended to {output_file}")

if __name__ == "__main__":
    main()
