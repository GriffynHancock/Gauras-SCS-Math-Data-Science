import json
import os
from pathlib import Path
import PyPDF2
from ebooklib import epub
from bs4 import BeautifulSoup
from pysimilar import compare
import re

class HomogeneityAnalyzer:
    def __init__(self, report_path='entropy_report_raw.json'):
        with open(report_path, 'r') as f:
            self.report = json.load(f)
        self.samples_dir = Path('entropy_samples')
        self.output_dir = Path('homogeneity_test')
        self.output_dir.mkdir(exist_ok=True)

    def clean_text(self, text):
        # Basic cleaning for comparison
        text = re.sub(r'\s+', ' ', text)
        return text.strip().lower()

    def extract_first_10_pdf(self, file_path):
        text = ""
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                pages = reader.pages[:10]
                for p in pages:
                    text += p.extract_text() + "\n"
        except Exception as e:
            text = f"Error: {e}"
        return text

    def extract_first_10_epub(self, file_path):
        text = ""
        try:
            book = epub.read_epub(str(file_path))
            docs = list(book.get_items_of_type(os.SEEK_SET)) # Hack to get items
            # Better way to get documents
            items = list(book.get_items())
            count = 0
            for item in items:
                if item.get_type() == 9: # DOCUMENT
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text += soup.get_text() + "\n"
                    count += 1
                    if count >= 10: break
        except Exception as e:
            text = f"Error: {e}"
        return text

    def extract_html(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                return soup.get_text()
        except Exception as e:
            return f"Error: {e}"

    def run(self):
        analysis_results = {}
        
        for cat, samples in self.report.items():
            print(f"🧐 Analyzing homogeneity for {cat}...")
            texts = []
            for i, sample in enumerate(samples):
                ext = Path(sample['url']).suffix.lower()
                file_path = self.samples_dir / f"{cat}_{i}{ext}"
                if not file_path.exists():
                    # Handle articles which might have different extensions in my script
                    if sample['fingerprint']['mime'] == 'text/html':
                        file_path = self.samples_dir / f"{cat}_{i}.html"

                content = ""
                if 'pdf' in sample['fingerprint']['mime']:
                    content = self.extract_first_10_pdf(file_path)
                elif 'epub' in sample['fingerprint']['mime'] or 'zip' in sample['fingerprint']['mime']:
                    content = self.extract_first_10_epub(file_path)
                else:
                    content = self.extract_html(file_path)
                
                cleaned = self.clean_text(content)
                texts.append(cleaned)
                
                # Save sample text
                (self.output_dir / f"{cat}_{i}.txt").write_text(content, encoding='utf-8')

            # Similarity Matrix
            matrix = []
            if len(texts) > 1:
                for t1 in texts:
                    row = []
                    for t2 in texts:
                        try:
                            score = compare(t1, t2)
                            row.append(score)
                        except:
                            row.append(0.0)
                    matrix.append(row)
            
            analysis_results[cat] = {
                'similarity_matrix': matrix,
                'avg_similarity': sum([sum(row) for row in matrix]) / (len(matrix)**2) if matrix else 1.0
            }
            print(f"  Avg Similarity: {analysis_results[cat]['avg_similarity']:.2f}")

        with open('homogeneity_report.json', 'w') as f:
            json.dump(analysis_results, f, indent=2)
        print("\n✅ Homogeneity report saved to homogeneity_report.json")

if __name__ == "__main__":
    analyzer = HomogeneityAnalyzer()
    analyzer.run()
