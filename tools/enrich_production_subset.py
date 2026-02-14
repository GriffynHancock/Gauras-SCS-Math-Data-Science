import json
import requests
import sys
import os
from pathlib import Path
from collections import defaultdict

class SubsetEnricher:
    def __init__(self, api_url="http://127.0.0.1:8085/v1/chat/completions"):
        self.api_url = api_url
        try:
            self.system_prompt = Path("system_prompt.txt").read_text(encoding='utf-8')
        except FileNotFoundError:
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
            response = requests.post(self.api_url, json=payload, timeout=120)
            if response.status_code != 200: return None
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            if content.startswith("```json"): content = content[7:-3].strip()
            elif content.startswith("```"): content = content[3:-3].strip()
            return json.loads(content)
        except: return None

def main():
    enricher = SubsetEnricher()
    input_file = Path("data/processed/granular_chunks.json")
    output_file = Path("data/processed/production_subset_enriched.jsonl")

    if output_file.exists(): output_file.unlink()

    target_books = [
        "en-RevealedTruth", 
        "en-Śaraṇāgati", 
        "en-SearchForŚrīKṛṣṇa",
        "en-ŚrīGuruandHisGrace",
        "en-ŚrīŚrīPrapanna-jīvanāmṛtam",
        "en-GoldenVolcanoofDivineLove",
        "en-HomeComfort",
        "en-InnerFulfilment"
    ]
    
    print(f"📖 Loading production chunks...")
    with open(input_file, 'r', encoding='utf-8') as f:
        all_chunks = json.load(f)

    subset_chunks = [c for c in all_chunks if c['metadata']['book_id'] in target_books]
    
    # Import chunk_songs from the tools directory
    sys.path.append(str(Path("tools").absolute()))
    try:
        from chunk_songs import SongChunker
        song_chunker = SongChunker()
    except ImportError:
        print("❌ Could not import SongChunker from tools/chunk_songs.py")
        return

    gitanjali_dir = Path("gaudiya_gitanjali")
    
    print("🎵 Processing ALL songs...")
    song_count = 0
    for root, dirs, files in os.walk(gitanjali_dir):
        for file in files:
            if file.endswith(".txt"):
                author = "Unknown"
                if "Śrīdhar" in root: author = "Srila B.R. Sridhar Maharaj"
                elif "Govinda" in root: author = "Srila B.S. Govinda Maharaj"
                elif "Bhaktivinoda" in root: author = "Srila Bhakti Vinod Thakur"
                
                new_song_chunks = song_chunker.process_song_file(Path(root) / file, author=author)
                for sc in new_song_chunks:
                    res = enricher.enrich_chunk(sc['text'])
                    if res:
                        sc['metadata'].update(res)
                        with open(output_file, 'a', encoding='utf-8') as f_out:
                            f_out.write(json.dumps(sc, ensure_ascii=False) + "\n")
                        song_count += 1
                        sys.stdout.write(f"\r  ✅ Songs: {song_count}")
                        sys.stdout.flush()

    print(f"\n📚 Processing {len(subset_chunks)} book chunks...")
    book_count = 0
    for chunk in subset_chunks:
        res = enricher.enrich_chunk(chunk['text'])
        if res:
            chunk['metadata'].update(res)
            with open(output_file, 'a', encoding='utf-8') as f_out:
                f_out.write(json.dumps(chunk, ensure_ascii=False) + "\n")
            book_count += 1
            if book_count % 10 == 0:
                sys.stdout.write(f"\r  ✅ Books: {book_count}/{len(subset_chunks)}")
                sys.stdout.flush()

    print(f"\n🎉 Production subset complete! Total: {song_count + book_count} chunks.")

if __name__ == "__main__":
    main()
