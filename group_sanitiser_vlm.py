import json
from pathlib import Path
import re
import PyPDF2
from ebooklib import epub
from bs4 import BeautifulSoup
from pdf2image import convert_from_path
from mlx_vlm import load, generate
from sanitise_english import EnglishSanitizer
import time

class GroupSanitizerVLM:
    def __init__(self, report_path='bulk_entropy_report.json'):
        with open(report_path, 'r') as f:
            self.report = json.load(f)
        self.english_sanitizer = EnglishSanitizer()
        self.output_dir = Path('mini_dataset_vlm')
        self.output_dir.mkdir(exist_ok=True)
        
        # Load VLM Singleton
        print("🚀 Loading PaddleOCR-VL-1.5-4bit (MLX)...")
        self.model, self.processor = load("mlx-community/PaddleOCR-VL-1.5-4bit")
        self.vlm_prompt = "<|begin_of_sentence|>User: <|IMAGE_START|><|IMAGE_PLACEHOLDER|><|IMAGE_END|><|image|>\nOCR with layout: \nAssistant:"

    def extract_epub(self, file_path):
        try:
            book = epub.read_epub(str(file_path))
            text = ""
            for item in book.get_items():
                if item.get_type() == 9: # DOCUMENT
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    text += soup.get_text() + "\n"
            return text
        except:
            return ""

    def extract_vlm_ocr(self, file_path, pages=(5, 6)):
        try:
            # Convert specified pages to images
            images = convert_from_path(file_path, first_page=pages[0], last_page=pages[1], dpi=200)
            text = ""
            for i, img in enumerate(images):
                temp_img = f"temp_ocr_{i}.png"
                img.save(temp_img)
                
                res = generate(
                    self.model, 
                    self.processor, 
                    self.vlm_prompt, 
                    temp_img, 
                    max_tokens=1024,
                    repetition_penalty=1.2
                )
                text += res.text + "\n"
                Path(temp_img).unlink() # Cleanup
            return text
        except Exception as e:
            print(f"    ❌ VLM OCR Error: {e}")
            return ""

    def extract_html(self, file_path):
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            soup = BeautifulSoup(content, 'html.parser')
            for s in soup(["script", "style"]):
                s.extract()
            return soup.get_text()
        except:
            return ""

    def process_mini_dataset(self):
        dataset_summary = []
        top_clusters = sorted(self.report['clusters'].items(), key=lambda x: len(x[1]), reverse=True)[:5]
        
        for cluster_id, filenames in top_clusters:
            print(f"📂 Cluster: {cluster_id}")
            samples = filenames[:3] 
            
            for fname in samples:
                f_info = next(f for f in self.report['files'] if f['filename'] == fname)
                file_path = Path(f_info['path'])
                
                print(f"  🧼 Processing {fname}...")
                raw_text = ""
                
                # BRANCHING LOGIC
                if 'indian_lang' in cluster_id:
                    raw_text = self.extract_vlm_ocr(file_path)
                elif 'pdf' in f_info['mime']:
                    try:
                        with open(file_path, 'rb') as f:
                            reader = PyPDF2.PdfReader(f)
                            for p in reader.pages[:20]:
                                raw_text += p.extract_text() or ""
                    except:
                        pass
                    
                    if len(raw_text.strip()) < 100:
                        print(f"    📸 Detect scan, running VLM OCR for {fname}...")
                        raw_text = self.extract_vlm_ocr(file_path)
                elif 'epub' in f_info['mime'] or 'zip' in f_info['mime']:
                    raw_text = self.extract_epub(file_path)
                elif 'html' in f_info['mime'] or 'text' in f_info['mime']:
                    raw_text = self.extract_html(file_path)
                
                clean_text = self.english_sanitizer.sanitise(raw_text)
                
                # SAVE
                dest_path = self.output_dir / f"{fname}.txt"
                dest_path.write_text(clean_text, encoding='utf-8')
                
                word_count = len(clean_text.split())
                print(f"    ✅ Saved {word_count} words.")
                
                dataset_summary.append({
                    'cluster': cluster_id,
                    'original': fname,
                    'status': 'processed' if word_count > 20 else 'warning_low_content'
                })
                
        with open('mini_dataset_vlm_report.json', 'w') as f:
            json.dump(dataset_summary, f, indent=2)

if __name__ == "__main__":
    gs = GroupSanitizerVLM()
    gs.process_mini_dataset()
