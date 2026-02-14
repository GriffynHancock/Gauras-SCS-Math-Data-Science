import json
import requests
import sys
from pathlib import Path
from collections import defaultdict

class MicroDatasetEnricher:
    def __init__(self, api_url="http://127.0.0.1:8085/v1/chat/completions"):
        self.api_url = api_url
        try:
            self.system_prompt = Path("system_prompt.txt").read_text(encoding='utf-8')
        except FileNotFoundError:
            print("⚠️ system_prompt.txt not found. Using default prompt.")
            self.system_prompt = "You are an expert Gaudiya Vaishnava theologian."

    def enrich_chunk(self, current_text):
        payload = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Analyze this text:\n\n{current_text}"}
            ],
            "temperature": 0.1
        }

        try:
            response = requests.post(self.api_url, json=payload, timeout=300)
            if response.status_code != 200:
                return None
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            if content.startswith("```json"): content = content[7:-3].strip()
            elif content.startswith("```"): content = content[3:-3].strip()
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return None
        except Exception as e:
            return None

def main():
    enricher = MicroDatasetEnricher()
    processed_dir = Path("data/micro_test/processed")
    
    # Process both book chunks and song chunks
    input_files = [processed_dir / "chunks.json", processed_dir / "song_chunks.json"]
    output_file = processed_dir / "enriched_chunks.jsonl"

    # If output file exists, delete it to start fresh for this test
    if output_file.exists():
        output_file.unlink()

    print(f"🌟 Starting Micro Enrichment with Songs...")
    
    total_processed = 0
    
    for input_file in input_files:
        if not input_file.exists():
            print(f"⚠️ Input file {input_file} not found, skipping.")
            continue
            
        print(f"📖 Processing {input_file.name}...")
        with open(input_file, 'r', encoding='utf-8') as f:
            all_chunks = json.load(f)

        # For book chunks, we still only take a sample (5 per book)
        if input_file.name == "chunks.json":
            chunks_by_book = defaultdict(list)
            for chunk in all_chunks:
                chunks_by_book[chunk['metadata']['book_id']].append(chunk)
            
            target_chunks = []
            for book_id, chunks in chunks_by_book.items():
                start_idx = max(0, (len(chunks) - 5) // 2)
                target_chunks.extend(chunks[start_idx:start_idx + 5])
        else:
            # For songs, process ALL generated manual chunks
            target_chunks = all_chunks

        for chunk in target_chunks:
            result = enricher.enrich_chunk(chunk['text'])
            
            if result:
                chunk['metadata'].update(result)
                with open(output_file, 'a', encoding='utf-8') as f_out:
                    f_out.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                total_processed += 1
                sys.stdout.write(f"\r    ✅ Processed {total_processed} total chunks...")
                sys.stdout.flush()

    print(f"\n🎉 Enrichment complete! Saved {total_processed} chunks to {output_file}")

if __name__ == "__main__":
    main()
