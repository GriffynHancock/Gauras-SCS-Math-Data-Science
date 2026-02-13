import json
import requests
import os
from pathlib import Path
from tqdm import tqdm

class SongEnricher:
    def __init__(self, api_url="http://127.0.0.1:8083/v1/chat/completions"):
        self.api_url = api_url
        self.system_prompt = Path("system_prompt.txt").read_text(encoding='utf-8')

    def analyze_whole_song(self, full_text):
        prompt = f"""Analyze this entire Gaudiya Vaishnava song.
Identify:
1. Global Entities: Specific Persons, Deities, Places, Texts.
2. Main Themes: Top 3 from established taxonomy.
3. Primary Tattva: One category based on rules.

SONG TEXT:
{full_text}

JSON format:
{{
  "global_entities": [],
  "main_themes": [],
  "primary_tattva": "",
  "song_summary": ""
}}"""
        payload = {
            "messages": [
                {"role": "system", "content": "You are an expert Gaudiya Vaishnava scholar. Return ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }
        try:
            response = requests.post(self.api_url, json=payload, timeout=600)
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            if content.startswith("```json"): content = content[7:-3].strip()
            elif content.startswith("```"): content = content[3:-3].strip()
            return json.loads(content)
        except: return None

def process_songs():
    enricher = SongEnricher()
    gitanjali_dir = Path("gaudiya_gitanjali")
    output_file = Path("data/processed/enriched_songs.jsonl")
    
    if output_file.exists(): output_file.unlink()

    song_files = list(gitanjali_dir.rglob("*.txt"))
    print(f"🎵 Processing {len(song_files)} songs...")

    for song_file in tqdm(song_files):
        try:
            text = song_file.read_text(encoding='utf-8')
            # 1. Get song-level metadata
            song_meta = enricher.analyze_whole_song(text)
            if not song_meta: continue

            # 2. Split into verses (rough heuristic for now)
            lines = text.split('
')
            verses = []
            current_verse = []
            for line in lines:
                if line.strip():
                    current_verse.append(line)
                elif current_verse:
                    verses.append("
".join(current_verse))
                    current_verse = []
            if current_verse: verses.append("
".join(current_verse))

            # 3. Save each verse with song-level context
            for i, verse_text in enumerate(verses):
                chunk = {
                    "id": f"{song_file.stem}_v{i+1}",
                    "text": verse_text,
                    "metadata": {
                        "song_title": song_file.stem,
                        "verse_num": i + 1,
                        "category": "song",
                        "author": song_file.parent.name,
                        **song_meta
                    }
                }
                with open(output_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(chunk, ensure_ascii=False) + "
")
        except: continue

    print(f"✅ Enriched songs saved to {output_file}")

if __name__ == "__main__":
    process_songs()
