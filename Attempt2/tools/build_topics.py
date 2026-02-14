import chromadb
import numpy as np
import json
import requests
import umap
from sklearn.cluster import HDBSCAN
from collections import defaultdict
from pathlib import Path
from tqdm import tqdm

class TopicBuilder:
    def __init__(self, api_url="http://127.0.0.1:8085/v1/chat/completions"):
        self.client = chromadb.PersistentClient(path="chroma_db")
        self.chunks_col = self.client.get_collection("micro_chunks_collection")
        
        try:
            self.client.delete_collection("micro_topics_collection")
        except:
            pass
        self.topics_col = self.client.create_collection(
            "micro_topics_collection",
            metadata={"hnsw:space": "cosine"}
        )
        self.api_url = api_url
        self.topic_records = []
        
    def load_data(self):
        print("📥 Loading embeddings from ChromaDB...")
        data = self.chunks_col.get(include=['embeddings', 'metadatas', 'documents'])
        self.ids = data['ids']
        self.embeddings = np.array(data['embeddings'])
        self.metadatas = data['metadatas']
        self.documents = data['documents']
        print(f"   Loaded {len(self.ids)} chunks.")

    def cluster_data(self):
        print("🧮 Reducing dimensionality (UMAP)...")
        if len(self.ids) < 15:
            reduced_embeddings = self.embeddings
        else:
            umap_reducer = umap.UMAP(
                n_neighbors=15,
                n_components=5,
                min_dist=0.0,
                metric='cosine'
            )
            reduced_embeddings = umap_reducer.fit_transform(self.embeddings)

        print("🔍 Clustering (HDBSCAN)...")
        clusterer = HDBSCAN(
            min_cluster_size=3,
            min_samples=1,
            metric='euclidean', 
            cluster_selection_method='eom'
        )
        self.labels = clusterer.fit_predict(reduced_embeddings)
        
        n_clusters = len(set(self.labels)) - (1 if -1 in self.labels else 0)
        print(f"   Found {n_clusters} clusters.")
        
    def synthesize_topics(self):
        print("🧪 Synthesizing topics...")
        self.topic_records = []
        
        clusters = defaultdict(list)
        for i, label in enumerate(self.labels):
            if label == -1: continue
            clusters[label].append(i)
            
        for label, indices in tqdm(clusters.items(), desc="Processing topics"):
            cluster_embeddings = self.embeddings[indices]
            if len(cluster_embeddings) == 0: continue
            
            centroid_mean = np.mean(cluster_embeddings, axis=0)
            norm = np.linalg.norm(centroid_mean)
            if norm > 1e-9:
                centroid_mean = centroid_mean / norm
            
            distances = np.linalg.norm(cluster_embeddings - centroid_mean, axis=1)
            medoid_idx = indices[np.argmin(distances)]
            medoid_id = self.ids[medoid_idx]
            
            sorted_pairs = sorted(zip(distances, indices), key=lambda x: x[0])
            sorted_indices = [idx for dist, idx in sorted_pairs]
            rep_indices = sorted_indices[:5]
            
            # AGGREGATE SIGNALS
            cluster_metas = [self.metadatas[i] for i in indices]
            is_lila_count = sum(1 for m in cluster_metas if m.get('is_lila', False))
            chrono_p_count = sum(1 for m in cluster_metas if m.get('chronology_personal', False))
            chrono_l_count = sum(1 for m in cluster_metas if m.get('chronology_place', False))
            
            # If > 30% of chunks have the flag, mark the topic
            threshold = 0.3
            is_lila_topic = (is_lila_count / len(indices)) > threshold
            is_chrono_p_topic = (chrono_p_count / len(indices)) > threshold
            is_chrono_l_topic = (chrono_l_count / len(indices)) > threshold
            
            topic_meta = self.generate_label(
                [self.ids[i] for i in rep_indices], 
                [self.metadatas[i] for i in rep_indices], 
                [self.documents[i] for i in rep_indices],
                signals={"is_lila": is_lila_topic, "chrono_p": is_chrono_p_topic, "chrono_l": is_chrono_l_topic}
            )
            
            if not isinstance(topic_meta, dict):
                topic_meta = {"label": f"Topic {label}", "description": "N/A", "keywords": []}

            topic_record = {
                "topic_id": f"topic_{label:03d}",
                "label": topic_meta.get('label', f"Topic {label}"),
                "description": topic_meta.get('description', "N/A"),
                "centroid_embedding": centroid_mean.tolist(),
                "chunk_ids": [self.ids[i] for i in indices],
                "size": len(indices),
                "medoid_chunk_id": medoid_id,
                "rep_chunk_ids": [self.ids[i] for i in rep_indices],
                "keywords": topic_meta.get('keywords', []),
                "is_lila": is_lila_topic,
                "chronology_personal": is_chrono_p_topic,
                "chronology_place": is_chrono_l_topic
            }
            self.topic_records.append(topic_record)
            
    def generate_label(self, rep_ids, rep_metas, rep_docs, signals=None):
        context_texts = []
        for i in range(len(rep_ids)):
            summary = rep_metas[i].get('summary', '')
            if not summary:
                summary = rep_docs[i][:200]
            context_texts.append(f"- {summary}")
        context_str = "\n".join(context_texts)
        
        signal_str = ""
        if signals:
            if signals['is_lila']: signal_str += "\nNOTE: This topic heavily features Divine Lila (Pastimes)."
            if signals['chrono_p']: signal_str += "\nNOTE: This topic contains significant biographical/chronological data."
            if signals['chrono_l']: signal_str += "\nNOTE: This topic contains historical information about holy places."

        prompt = f"Summaries:\n{context_str}{signal_str}\n\nProvide JSON: {{ 'label': '...', 'description': '...', 'keywords': [...] }}"
        
        try:
            response = requests.post(self.api_url, json={
                "messages": [
                    {"role": "system", "content": "You are a taxonomist. Return ONLY JSON."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1
            }, timeout=30)
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content'].strip()
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                parsed = json.loads(content)
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed[0]
                return parsed
        except:
            pass
        return {"label": "Unknown", "description": "N/A", "keywords": []}

    def save_topics(self):
        if not self.topic_records: return
        print(f"💾 Saving {len(self.topic_records)} topics...")
        self.topics_col.add(
            ids=[r['topic_id'] for r in self.topic_records],
            embeddings=[r['centroid_embedding'] for r in self.topic_records],
            metadatas=[{
                "label": str(r['label']),
                "description": str(r['description']),
                "size": r['size'],
                "keywords": ", ".join(r['keywords']) if isinstance(r['keywords'], list) else str(r['keywords']),
                "is_lila": r['is_lila'],
                "chronology_personal": r['chronology_personal'],
                "chronology_place": r['chronology_place']
            } for r in self.topic_records]
        )
        with open("data/micro_test/processed/topics.json", "w", encoding='utf-8') as f:
            json.dump(self.topic_records, f, indent=2, ensure_ascii=False)

def main():
    builder = TopicBuilder()
    builder.load_data()
    builder.cluster_data()
    builder.synthesize_topics()
    builder.save_topics()

if __name__ == "__main__":
    main()
