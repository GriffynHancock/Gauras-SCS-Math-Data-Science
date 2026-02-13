import json
import requests
from pathlib import Path

class ComparativeEnricher:
    def __init__(self, api_url="http://127.0.0.1:8085/v1/chat/completions"):
        self.api_url = api_url
        self.system_prompt = Path("system_prompt.txt").read_text(encoding='utf-8')

    def enrich(self, text):
        user_msg = "Analyze this text:\n\n" + text
        payload = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_msg}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }
        try:
            resp = requests.post(self.api_url, json=payload, timeout=60)
            return resp.json()['choices'][0]['message']['content']
        except: return "{}"

def main():
    enricher = ComparativeEnricher()
    # IDs from Hit 1 and Hit 2
    ids_to_compare = ["en-GoldenReflections_ch00084", "en-GoldenReflections_ch00085", "en-GoldenReflections_ch00086", "en-Śaraṇāgati_ch00044"]
    
    input_file = Path("data/processed/refined_robust_chunks.json")
    with open(input_file, 'r') as f:
        all_chunks = json.load(f)
    
    comparison_output = []
    
    for cid in ids_to_compare:
        chunk = next((c for c in all_chunks if c['id'] == cid), None)
        if not chunk: continue
        
        print(f"🔄 Enhancing {cid}...")
        llm_meta = enricher.enrich(chunk['text'])
        
        comparison_output.append(f"CHUNK ID: {cid}")
        comparison_output.append("="*40)
        comparison_output.append("TEXT:")
        comparison_output.append(chunk['text'])
        comparison_output.append("-" * 20)
        comparison_output.append("ORIGINAL (HEURISTIC) METADATA:")
        comparison_output.append(json.dumps(chunk['metadata'], indent=2))
        comparison_output.append("-" * 20)
        comparison_output.append("LLM ENHANCED METADATA:")
        comparison_output.append(llm_meta)
        comparison_output.append("\n" + "#"*60 + "\n")

    Path("enhancement_comparison.txt").write_text("\n".join(comparison_output), encoding='utf-8')
    print("✅ Comparison saved to enhancement_comparison.txt")

if __name__ == "__main__":
    main()
