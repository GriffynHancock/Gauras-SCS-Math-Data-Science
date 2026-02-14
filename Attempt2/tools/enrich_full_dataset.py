import json
import requests
import sys
import os
import time
from pathlib import Path
from collections import defaultdict

class FullDatasetEnricher:
    def __init__(self, api_url="http://127.0.0.1:8085/v1/chat/completions"):
        self.api_url = api_url
        try:
            self.system_prompt = Path("system_prompt.txt").read_text(encoding='utf-8')
        except FileNotFoundError:
            print("❌ system_prompt.txt not found.")
            sys.exit(1)

    def enrich_chunk(self, current_text):
        payload = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Analyze this text:

{current_text}"}
            ],
            "temperature": 0.1
        }

        try:
            response = requests.post(self.api_url, json=payload, timeout=60)
            if response.status_code != 200:
                return None
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            if content.startswith("```json"): content = content[7:-3].strip()
            elif content.startswith("```"): content = content[3:-3].strip()
            
            return json.loads(content)
        except Exception:
            return None

def process():
    enricher = FullDatasetEnricher()
    
    # We use granular_chunks as the source as it has the best initial typing
    input_file = Path("data/processed/granular_chunks.json")
    output_file = Path("data/processed/full_enriched_chunks.jsonl")
    checkpoint_file = Path("data/processed/enrichment_checkpoint.txt")

    if not input_file.exists():
        print(f"❌ Input file {input_file} not found.")
        return

    print(f"📖 Loading chunks from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        all_chunks = json.load(f)

    # Resume from checkpoint if exists
    start_index = 0
    if checkpoint_file.exists():
        try:
            start_index = int(checkpoint_file.read_text().strip())
            print(f"🔄 Resuming from index {start_index}")
        except:
            pass

    print(f"🌟 Starting production enrichment of {len(all_chunks)} chunks...")
    print(f"📊 Target: {output_file}")
    
    # Use append mode for output
    with open(output_file, 'a', encoding='utf-8') as f_out:
        for i in range(start_index, len(all_chunks)):
            chunk = all_chunks[i]
            
            # Skip chunks with very little text
            if len(chunk['text'].split()) < 10:
                # Still write it but with minimal metadata to keep indices consistent if needed
                # Actually, better to just enrich everything or skip and record skip
                pass

            result = enricher.enrich_chunk(chunk['text'])
            
            if result:
                chunk['metadata'].update(result)
                f_out.write(json.dumps(chunk, ensure_ascii=False) + "
")
                
                # Update checkpoint every 10 chunks
                if i % 10 == 0:
                    checkpoint_file.write_text(str(i))
                    f_out.flush()
                    
                sys.stdout.write(f"🚀 Progress: {i}/{len(all_chunks)} ({ (i/len(all_chunks))*100 :.2f}%)")
                sys.stdout.flush()
            else:
                # Retry once after a short sleep
                time.sleep(2)
                result = enricher.enrich_chunk(chunk['text'])
                if result:
                    chunk['metadata'].update(result)
                    f_out.write(json.dumps(chunk, ensure_ascii=False) + "
")
                else:
                    print(f"
⚠️ Failed to enrich chunk {chunk['id']} at index {i}")

    print(f"
🎉 FULL ENRICHMENT COMPLETE!")
    if checkpoint_file.exists():
        checkpoint_file.unlink()

if __name__ == "__main__":
    process()
