import json
import os
import hashlib
import math
import requests
import magic
import pikepdf
from epub_meta import get_epub_metadata
from pathlib import Path
import time

class EntropyAnalyzer:
    def __init__(self, index_path='source_index.json'):
        with open(index_path, 'r') as f:
            self.index = json.load(f)
        self.samples_dir = Path('entropy_samples')
        self.samples_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})

    def calculate_entropy(self, data):
        if not data:
            return 0
        entropy = 0
        for x in range(256):
            p_x = float(data.count(x))/len(data)
            if p_x > 0:
                entropy += - p_x * math.log(p_x, 2)
        return entropy

    def get_fingerprint(self, file_path):
        with open(file_path, 'rb') as f:
            data = f.read()
        
        sha256 = hashlib.sha256(data).hexdigest()
        mime = magic.from_buffer(data, mime=True)
        ent = self.calculate_entropy(data)
        
        return {
            'sha256': sha256,
            'mime': mime,
            'entropy': ent,
            'size': len(data)
        }

    def get_pdf_metadata(self, file_path):
        try:
            with pikepdf.open(file_path) as pdf:
                meta = {
                    'version': pdf.pdf_version,
                    'is_optimized': pdf.is_linearized,
                    'page_count': len(pdf.pages),
                }
                # Add more metadata if available
                docinfo = pdf.docinfo
                for key, val in docinfo.items():
                    meta[str(key)] = str(val)
                return meta
        except Exception as e:
            return {'error': str(e)}

    def get_epub_metadata(self, file_path):
        try:
            data = get_epub_metadata(str(file_path))
            return {
                'title': data.title,
                'authors': data.authors,
                'publication_date': data.publication_date,
                'language': data.language,
                'version': data.version if hasattr(data, 'version') else 'unknown'
            }
        except Exception as e:
            return {'error': str(e)}

    def run_analysis(self, samples_per_cat=3):
        results = {}
        
        # Group by category
        cats = {}
        for src in self.index['sources']:
            cat = src['category']
            if cat not in cats: cats[cat] = []
            cats[cat].append(src)
        
        for cat, sources in cats.items():
            print(f"🔬 Sampling {cat}...")
            results[cat] = []
            # Take a few samples
            samples = sources[:samples_per_cat] 
            
            for i, src in enumerate(samples):
                ext = '.html' if src['type'] == 'html_article' else f".{src['type']}"
                filename = f"{cat}_{i}{ext}"
                file_path = self.samples_dir / filename
                
                print(f"  📥 Downloading {src['url']}...")
                try:
                    resp = self.session.get(src['url'], timeout=30)
                    resp.raise_for_status()
                    with open(file_path, 'wb') as f:
                        f.write(resp.content)
                    
                    analysis = {
                        'title': src['title'],
                        'url': src['url'],
                        'fingerprint': self.get_fingerprint(file_path)
                    }
                    
                    if src['type'] == 'pdf':
                        analysis['metadata'] = self.get_pdf_metadata(file_path)
                    elif src['type'] == 'epub':
                        analysis['metadata'] = self.get_epub_metadata(file_path)
                    
                    results[cat].append(analysis)
                    time.sleep(1)
                except Exception as e:
                    print(f"  ❌ Error: {e}")
                    
        with open('entropy_report_raw.json', 'w') as f:
            json.dump(results, f, indent=2)
        print("\n📊 Raw entropy report saved to entropy_report_raw.json")

if __name__ == "__main__":
    analyzer = EntropyAnalyzer()
    analyzer.run_analysis()
