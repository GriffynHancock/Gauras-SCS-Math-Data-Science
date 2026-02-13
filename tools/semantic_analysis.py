import os
import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np

class SemanticAnalyzer:
    def __init__(self, dataset_dir='mini_dataset'):
        self.dataset_dir = Path(dataset_dir)
        self.texts = []
        self.filenames = []

    def load_data(self):
        print("📂 Loading mini-dataset for semantic analysis...")
        for txt_path in self.dataset_dir.glob('*.txt'):
            content = txt_path.read_text(encoding='utf-8')
            if len(content) > 100: # Ignore empty/ocr-pending
                self.texts.append(content)
                self.filenames.append(txt_path.name)
        print(f"  ✅ Loaded {len(self.texts)} valid text samples.")

    def analyze(self, num_clusters=3):
        if not self.texts:
            print("❌ No text data to analyze.")
            return

        print(f"🤖 Vectorizing and clustering into {num_clusters} topics...")
        vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        X = vectorizer.fit_transform(self.texts)
        
        kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
        kmeans.fit(X)
        
        # Get top words per cluster
        order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
        terms = vectorizer.get_feature_names_out()
        
        results = {
            'clusters': []
        }
        
        for i in range(num_clusters):
            top_words = [terms[ind] for ind in order_centroids[i, :10]]
            cluster_files = [self.filenames[j] for j, label in enumerate(kmeans.labels_) if label == i]
            
            results['clusters'].append({
                'id': i,
                'top_words': top_words,
                'files': cluster_files
            })
            
            print(f"\n✨ Topic Cluster {i}:")
            print(f"  Top Words: {', '.join(top_words)}")
            print(f"  Samples: {cluster_files[:3]}")

        with open('semantic_analysis_report.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📊 Semantic analysis report saved to semantic_analysis_report.json")

if __name__ == "__main__":
    analyzer = SemanticAnalyzer()
    analyzer.load_data()
    analyzer.analyze()
