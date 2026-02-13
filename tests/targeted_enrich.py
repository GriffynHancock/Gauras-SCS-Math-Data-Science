import json
import requests
from pathlib import Path

class TargetedEnricher:
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
            resp = requests.post(self.api_url, json=payload, timeout=120)
            return resp.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"{{\"error\": \"{str(e)}\"}}"

def main():
    enricher = TargetedEnricher()
    target_ids = ["en-GoldenReflections_ch00084", "en-GoldenReflections_ch00085", "en-GoldenReflections_ch00086"]
    
    input_file = Path("data/processed/refined_robust_chunks.json")
    with open(input_file, 'r') as f:
        all_chunks = json.load(f)
    
    diff_report = ["TARGETED ENHANCEMENT DIFFERENCE REPORT", "="*50, ""]
    
    for cid in target_ids:
        chunk = next((c for c in all_chunks if c['id'] == cid), None)
        if not chunk: continue
        
        print(f"🔄 LLM processing {cid}...")
        new_meta_json = enricher.enrich(chunk['text'])
        new_meta = json.loads(new_meta_json)
        
        diff_report.append(f"CHUNK: {cid}")
        diff_report.append("-" * 30)
        diff_report.append(f"PREVIOUS TYPE: {chunk['metadata'].get('type')}")
        diff_report.append(f"NEW CATEGORY:  {new_meta.get('category')}")
        diff_report.append(f"HAS SLOKA:     {new_meta.get('has_sloka')}")
        diff_report.append(f"SCRIPTURE:     {new_meta.get('scripture_source')}")
        diff_report.append(f"ENTITIES:      {', '.join(new_meta.get('entities', []))}")
        diff_report.append(f"SUMMARY:       {new_meta.get('summary')}")
        diff_report.append("\n" + "."*50 + "\n")

    Path("targeted_enhancement_diff.txt").write_text("\n".join(diff_report), encoding='utf-8')
    print("✅ Results saved to targeted_enhancement_diff.txt")

if __name__ == "__main__":
    main()
