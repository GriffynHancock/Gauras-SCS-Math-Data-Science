import json
import requests
from pathlib import Path

def synthesize():
    api_url = "http://127.0.0.1:8085/v1/chat/completions"
    rag_file = Path("youth_kirtan_rag.txt")
    
    if not rag_file.exists():
        print("❌ RAG input file not found.")
        return

    context = rag_file.read_text(encoding='utf-8')
    
    user_query = "I went to a youth kirtan recently by a guy named Gaurahari Das, during it he repeatedly talked about saranagati and how important it is. even, one ISKCON girl connected saranagati with the 4 regulative principles, but he dissagreed, saying that even brahman samadhi can be bad for saranagati. at other kirtan groups ive heard saranagati described as like an emotion, but he was saying its actually an active thing, and connected it with yajna, saying that we need to offer everything we have into the fire of hari kirtan. can you explain this to me?"

    prompt = f"You are a senior scholar of the Sri Chaitanya Saraswat Math. Use the provided RAG CONTEXT below to answer the USER QUERY. Ensure your answer is sophisticated, rooted in the teachings of Srila Sridhar Maharaj and Srila Govinda Maharaj, and includes specific citations from the provided context.\n\nUSER QUERY:\n{user_query}\n\nRAG CONTEXT:\n{context}\n\nANSWER:"

    payload = {
        "messages": [
            {"role": "system", "content": "You are a specialized theological assistant for Gaudiya Vaishnava ontology."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 2048
    }

    print("🚀 Synthesizing sophisticated answer with LLM...")
    try:
        response = requests.post(api_url, json=payload, timeout=600)
        answer = response.json()['choices'][0]['message']['content']
        
        output_file = Path("youth_kirtan_rag_enhanced.txt")
        output_file.write_text(answer, encoding='utf-8')
        print(f"✅ Enhanced result saved to {output_file}")
    except Exception as e:
        print(f"❌ Error during synthesis: {e}")

if __name__ == "__main__":
    synthesize()
