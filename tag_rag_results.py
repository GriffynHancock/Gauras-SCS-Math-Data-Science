import json
import requests
import re
from pathlib import Path

class LiveTagger:
    def __init__(self, api_url="http://127.0.0.1:8085/v1/chat/completions"):
        self.api_url = api_url
        self.system_prompt = Path("system_prompt.txt").read_text(encoding='utf-8')

    def tag(self, text):
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
        except: return "{}"

def main():
    tagger = LiveTagger()
    rag_input = Path("youth_kirtan_rag.txt")
    output_file = Path("youth_kirtan_rag_enhanced.txt")
    
    if not rag_input.exists():
        print("❌ Input RAG file not found.")
        return

    content = rag_input.read_text(encoding='utf-8')
    chunk_ids = re.findall(r'\[ID: (.*?)\]', content)
    chunk_ids = list(dict.fromkeys(chunk_ids)) 

    with open("data/processed/refined_robust_chunks.json", 'r') as f:
        all_chunks = json.load(f)

    enhanced_output = ["=== LLM ENHANCED RAG VIEW (POST-HOC) ===", "="*60, ""]

    for cid in chunk_ids:
        chunk = next((c for c in all_chunks if c['id'] == cid), None)
        if not chunk: continue

        print(f"🔄 Live Tagging: {cid}...")
        raw_llm_json = tagger.tag(chunk['text'])
        llm_meta = json.loads(raw_llm_json)

        has_sloka_str = "YES" if llm_meta.get('has_sloka') else "NO"
        category = llm_meta.get('category', 'PROSE').upper()
        
        enhanced_output.append(f"--- CHUNK: {cid} ---")
        enhanced_output.append(f"[{category}] [HAS SLOKA: {has_sloka_str}] [SCRIPTURE: {llm_meta.get('scripture_source')}]")
        enhanced_output.append(f"ENTITIES: {', '.join(llm_meta.get('entities', []))}")
        enhanced_output.append(f"SUMMARY: {llm_meta.get('summary')}")
        enhanced_output.append("-" * 30)
        enhanced_output.append(chunk['text'])
        enhanced_output.append("\n" + "."*60 + "\n")

    output_file.write_text("\n".join(enhanced_output), encoding='utf-8')
    print(f"✅ Enhanced results saved to {output_file}")

if __name__ == "__main__":
    main()
