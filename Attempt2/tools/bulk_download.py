import json
import requests
import time
from pathlib import Path
from urllib.parse import urlparse

class BulkDownloader:
    def __init__(self, index_path='source_index.json', base_dir='scsmath_library'):
        with open(index_path, 'r') as f:
            self.index = json.load(f)
        self.base_dir = Path(base_dir)
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        
        # Setup directories
        for cat in ['english_pdfs', 'english_epubs', 'indian_lang_pdfs', 'misc_articles']:
            (self.base_dir / cat).mkdir(parents=True, exist_ok=True)

    def download_all(self):
        sources = self.index['sources']
        total = len(sources)
        print(f"🚀 Starting bulk download of {total} sources...")
        
        for i, src in enumerate(sources, 1):
            cat = src['category']
            url = src['url']
            
            # Create a clean filename
            parsed_url = urlparse(url)
            filename = Path(parsed_url.path).name
            if not filename or src['type'] == 'html_article':
                # Handle articles or extension-less URLs
                safe_title = "".join([c if c.isalnum() else "_" for c in src['title']])[:50]
                ext = '.html' if src['type'] == 'html_article' else Path(parsed_url.path).suffix or '.bin'
                filename = f"{safe_title}{ext}"
            
            dest_path = self.base_dir / cat / filename
            
            if dest_path.exists():
                print(f"[{i}/{total}] ⏭️ Skipping {filename} (Already exists)")
                continue
                
            print(f"[{i}/{total}] 📥 Downloading {url}...")
            try:
                resp = self.session.get(url, timeout=60)
                resp.raise_for_status()
                dest_path.write_bytes(resp.content)
                time.sleep(0.5) # Polite delay
            except Exception as e:
                print(f"  ❌ Error downloading {url}: {e}")
                
        print("\n✨ Bulk download complete.")

if __name__ == "__main__":
    downloader = BulkDownloader()
    downloader.download_all()
