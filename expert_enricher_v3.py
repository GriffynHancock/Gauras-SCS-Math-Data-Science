import json
import requests
import sys
from pathlib import Path
from collections import defaultdict

class ExpertEnricherV3:
    def __init__(self, api_url="http://127.0.0.1:8085/v1/chat/completions"):
        self.api_url = api_url
        self.system_prompt = Path("system_prompt.txt").read_text(encoding='utf-8')

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
            if response.status_code != 200: return None
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            # Basic cleanup for JSON
            if content.startswith("```json"): content = content[7:-3].strip()
            elif content.startswith("```"): content = content[3:-3].strip()
            
            return json.loads(content)
        except Exception as e:
            print(f"      ❌ Error: {e}")
            return None

def main():
    enricher = ExpertEnricherV3()
    input_file = Path("data/processed/refined_robust_chunks.json")
    output_file = Path("data/processed/v3_test_15_results.jsonl")

    if output_file.exists(): output_file.unlink()

    with open(input_file, 'r', encoding='utf-8') as f:
        all_chunks = json.load(f)

    # Pick 3 books and 5 chunks from each
    target_books = ["en-HomeComfort", "en-RevealedTruth", "en-SearchForŚrīKṛṣṇa"]
    
    print(f"🌟 Starting 15-chunk Expert V3 Verification...")
    
    total_processed = 0
    for book_id in target_books:
        print(f"  📖 Book: {book_id}")
        chunks_for_book = [c for c in all_chunks if c['metadata']['book_id'] == book_id]
        
        # Take 5 chunks from the middle to ensure good theological content
        start_idx = len(chunks_for_book) // 4
        for chunk in chunks_for_book[start_idx : start_idx + 5]:
            print(f"    🔄 Processing: {chunk['id']}")
            result = enricher.enrich_chunk(chunk['text'])
            if result:
                chunk['metadata'].update(result)
                with open(output_file, 'a', encoding='utf-8') as f_out:
                    f_out.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                total_processed += 1
                print(f"    ✅ [{total_processed}/15] Done.")
            sys.stdout.flush()

    print(f"🎉 Results saved to {output_file}")

if __name__ == "__main__":
    main()
