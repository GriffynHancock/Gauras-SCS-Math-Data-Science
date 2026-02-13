import json
import requests
import os
from pathlib import Path
from tqdm import tqdm

class RealLLMEnricher:
    def __init__(self, api_url="http://127.0.0.1:8080/v1/chat/completions", taxonomy=None):
        self.api_url = api_url
        self.taxonomy = taxonomy or []

    def enrich_chunk(self, chunk_text, chunk_type):
        # Specific instruction for transliteration if it's a sloka
        translit_instr = ""
        if chunk_type == "sloka":
            translit_instr = "3. Transliteration: Provide a clean IAST diacritic transliteration of the Sanskrit/Bengali text."
        else:
            translit_instr = "3. Transliteration: Set to null as this is prose/translation."

        prompt = f"""Analyze this Gaudiya Vaishnava text chunk and return ONLY a JSON object.
1. Entities: Specific persons (e.g., Krishna, Chaitanya Mahaprabhu, Bhakti Vinod Thakur) or places (e.g., Navadvip, Vrindavan).
2. Topics: Choose top 3 from {self.taxonomy} with a confidence score (0.0-1.0).
{translit_instr}

TEXT:
{chunk_text}

JSON format:
{{
  "entities": ["Name1", "Name2"],
  "topics": [{{"name": "TopicA", "score": 0.9}}, {{"name": "TopicB", "score": 0.7}}],
  "text_canonical": "IAST text or null"
}}"""

        payload = {
            "messages": [
                {"role": "system", "content": "You are an expert Gaudiya Vaishnava scholar familiar with Sri Chaitanya Saraswat Math. You return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }

        try:
            response = requests.post(self.api_url, json=payload, timeout=120)
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            
            # Basic cleanup of LLM output to ensure valid JSON
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
                
            return json.loads(content)
        except Exception as e:
            # print(f"Error processing chunk: {e}")
            return None

def main():
    taxonomy = [
        "Guru-tattva", "Saranagati", "Rasa-tattva", "Nama-tattva", 
        "Panchatattva", "Sadhana-bhakti", "Dham-tattva", "Vaisnava-aparadha",
        "Avatar-tattva", "Lila-katha", "Maya-samsara", "Prema-seva",
        "Vaishnava-etiquette", "Siddhanta", "Bhagavat-tattva"
    ]
    
    enricher = RealLLMEnricher(taxonomy=taxonomy)
    input_file = Path("data/processed/refined_granular_chunks.json")
    output_file = Path("data/processed/expert_enriched_chunks.jsonl")

    # Load chunks
    with open(input_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)

    # Check for existing progress
    processed_ids = set()
    if output_file.exists():
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    c = json.loads(line)
                    processed_ids.add(c['id'])
                except:
                    pass

    print(f"🌟 Starting LLM Enrichment. Total: {len(chunks)}, Already Processed: {len(processed_ids)}")
    
    # Process in batches to avoid losing progress
    limit = 100 
    count = 0
    
    for chunk in tqdm(chunks):
        if chunk['id'] in processed_ids:
            continue
            
        enriched_data = enricher.enrich_chunk(chunk['text'], chunk['metadata']['type'])
        if enriched_data:
            chunk['metadata'].update(enriched_data)
        
        with open(output_file, 'a', encoding='utf-8') as f_out:
            f_out.write(json.dumps(chunk, ensure_ascii=False) + "\n")
        
        count += 1
        if count >= limit:
            break

    print(f"✅ Batch complete. Results in {output_file}")

if __name__ == "__main__":
    main()
