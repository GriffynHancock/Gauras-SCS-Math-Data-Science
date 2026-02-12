import json
import random
from pathlib import Path
import re
from sanitise_english import EnglishSanitizer

class GroupSanitizer:
    def __init__(self, report_path='bulk_entropy_report.json'):
        with open(report_path, 'r') as f:
            self.report = json.load(f)
        self.english_sanitizer = EnglishSanitizer()
        self.output_dir = Path('mini_dataset')
        self.output_dir.mkdir(exist_ok=True)

    def get_top_clusters(self, n=5):
        clusters = self.report['clusters']
        # Sort by number of files in cluster
        sorted_clusters = sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)
        return sorted_clusters[:n]

    def process_mini_dataset(self):
        top_clusters = self.get_top_clusters()
        print(f"🏗️ Generating Mini-Dataset from top {len(top_clusters)} clusters...")
        
        dataset_summary = []
        
        for cluster_id, filenames in top_clusters:
            print(f"  📂 Processing Cluster: {cluster_id} ({len(filenames)} files)")
            # Sample 3
            samples = random.sample(filenames, min(3, len(filenames)))
            
            for fname in samples:
                # Find file info in report
                file_info = next(f for f in self.report['files'] if f['filename'] == fname)
                file_path = Path(file_info['path'])
                
                if not file_path.exists(): continue
                
                print(f"    🧼 Sanitising {fname}...")
                
                # Logic: If PDF and not Indian, use English Sanitizer
                # If Indian PDF, we'd need OCR (Skipping for now or just reporting)
                # If EPUB, use basic cleaning
                
                sanitised_text = ""
                status = "processed"
                
                if 'indian_lang' in cluster_id:
                    status = "ocr_pending"
                    sanitised_text = "[OCR REQUIRED FOR INDIAN LANGUAGE PDF]"
                elif 'pdf' in file_info['mime']:
                    try:
                        import PyPDF2
                        with open(file_path, 'rb') as f:
                            reader = PyPDF2.PdfReader(f)
                            raw_text = ""
                            # Only first 50 pages for the mini-dataset to keep it fast
                            for p in reader.pages[:50]:
                                raw_text += p.extract_text() + "\n"
                            sanitised_text = self.english_sanitizer.sanitise(raw_text)
                    except Exception as e:
                        status = f"error: {e}"
                elif 'epub' in file_info['mime'] or 'zip' in file_info['mime']:
                    sanitised_text = "[EPUB SANITISATION LOGIC PENDING]" # To be implemented
                
                # Save to dataset
                dest_path = self.output_dir / f"{fname}.txt"
                dest_path.write_text(sanitised_text, encoding='utf-8')
                
                dataset_summary.append({
                    'cluster': cluster_id,
                    'original': fname,
                    'status': status
                })
                
        with open('mini_dataset_report.json', 'w') as f:
            json.dump(dataset_summary, f, indent=2)
        print(f"\n✅ Mini-dataset generated in {self.output_dir}/")

if __name__ == "__main__":
    sanitiser = GroupSanitizer()
    sanitiser.process_mini_dataset()
