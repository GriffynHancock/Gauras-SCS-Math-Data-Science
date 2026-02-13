#!/usr/bin/env python3
"""
Sri Chaitanya Saraswat Math Publications Dataset Creator
=========================================================
Downloads and processes all publications from scsmath.org for LLM training.

This script:
1. Scrapes all PDF and EPUB links from the four main publication pages
2. Downloads all files systematically with proper organization
3. Extracts text from PDFs and EPUBs
4. Creates clean text files for LLM fine-tuning
5. Generates metadata and manifest files
"""

import os
import re
import time
import json
import hashlib
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Set, Tuple
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Optional dependencies for PDF/EPUB processing
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    print("⚠️  PyPDF2 not installed. Install with: pip install PyPDF2")

try:
    import ebooklib
    from ebooklib import epub
    EBOOKLIB_AVAILABLE = True
except ImportError:
    EBOOKLIB_AVAILABLE = False
    print("⚠️  ebooklib not installed. Install with: pip install ebooklib")

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("⚠️  BeautifulSoup not installed. Install with: pip install beautifulsoup4")


class SCSMathDownloader:
    """Downloads and organizes SCS Math publications."""
    
    # The four main publication pages
    PAGES = {
        'english_pdfs': 'https://scsmath.org/publications/publications-pdfs.html',
        'english_epubs': 'https://scsmath.org/publications/publications-epubs.html',
        'indian_lang_pdfs': 'https://scsmath.org/publications/publications-IndianLanguage-pdfs.html',
        'misc_articles': 'https://scsmath.com/docs/text_archive.html'
    }
    
    def __init__(self, base_dir: str = "./scsmath_dataset"):
        self.base_dir = Path(base_dir)
        self.downloads_dir = self.base_dir / "downloads"
        self.processed_dir = self.base_dir / "processed_text"
        self.metadata_dir = self.base_dir / "metadata"
        
        # Create directory structure
        for dir_path in [self.downloads_dir, self.processed_dir, self.metadata_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        # Subdirectories for organization
        (self.downloads_dir / "pdfs_english").mkdir(exist_ok=True)
        (self.downloads_dir / "epubs_english").mkdir(exist_ok=True)
        (self.downloads_dir / "pdfs_indian_languages").mkdir(exist_ok=True)
        (self.downloads_dir / "articles").mkdir(exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        self.manifest = {
            'created_at': datetime.now().isoformat(),
            'files': [],
            'statistics': {}
        }
        
    def scrape_links(self, page_url: str, base_url: str) -> List[Dict[str, str]]:
        """Scrape all PDF and EPUB links from a page."""
        print(f"📥 Scraping links from: {page_url}")
        
        try:
            response = self.session.get(page_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            links = []
            # Find all links that point to PDFs or EPUBs
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.endswith('.pdf') or href.endswith('.epub'):
                    full_url = urljoin(base_url, href)
                    
                    # Try to extract title from link text or nearby text
                    title = link.get_text(strip=True)
                    if not title or len(title) < 5:
                        # Look for title in parent elements
                        parent = link.find_parent(['td', 'tr', 'div'])
                        if parent:
                            title = parent.get_text(strip=True)[:200]
                    
                    links.append({
                        'url': full_url,
                        'filename': os.path.basename(urlparse(full_url).path),
                        'title': title,
                        'source_page': page_url
                    })
            
            print(f"✅ Found {len(links)} files on {page_url}")
            return links
            
        except Exception as e:
            print(f"❌ Error scraping {page_url}: {e}")
            return []
    
    def download_file(self, url: str, dest_path: Path, retries: int = 3) -> bool:
        """Download a file with retry logic."""
        for attempt in range(retries):
            try:
                print(f"⬇️  Downloading: {url}")
                response = self.session.get(url, timeout=60, stream=True)
                response.raise_for_status()
                
                with open(dest_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"✅ Downloaded: {dest_path.name}")
                return True
                
            except Exception as e:
                print(f"⚠️  Attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        return False
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF file."""
        if not PYPDF2_AVAILABLE:
            return "[PDF text extraction requires PyPDF2]"
        
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text_parts = []
                
                for page_num, page in enumerate(reader.pages):
                    try:
                        text = page.extract_text()
                        if text:
                            text_parts.append(f"\n--- Page {page_num + 1} ---\n{text}")
                    except Exception as e:
                        print(f"⚠️  Error extracting page {page_num + 1}: {e}")
                
                return "\n".join(text_parts)
                
        except Exception as e:
            print(f"❌ Error processing PDF {pdf_path.name}: {e}")
            return f"[Error extracting text: {e}]"
    
    def extract_text_from_epub(self, epub_path: Path) -> str:
        """Extract text from EPUB file."""
        if not EBOOKLIB_AVAILABLE:
            return "[EPUB text extraction requires ebooklib]"
        
        try:
            book = epub.read_epub(str(epub_path))
            text_parts = []
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    content = item.get_content()
                    soup = BeautifulSoup(content, 'html.parser')
                    text = soup.get_text(separator='\n', strip=True)
                    if text:
                        text_parts.append(text)
            
            return "\n\n".join(text_parts)
            
        except Exception as e:
            print(f"❌ Error processing EPUB {epub_path.name}: {e}")
            return f"[Error extracting text: {e}]"
    
    def process_file(self, file_path: Path) -> Dict:
        """Process a downloaded file and extract metadata."""
        print(f"📝 Processing: {file_path.name}")
        
        metadata = {
            'filename': file_path.name,
            'path': str(file_path.relative_to(self.base_dir)),
            'size_bytes': file_path.stat().st_size,
            'file_type': file_path.suffix[1:],
            'processed_at': datetime.now().isoformat()
        }
        
        # Extract text based on file type
        text_content = ""
        if file_path.suffix == '.pdf':
            text_content = self.extract_text_from_pdf(file_path)
        elif file_path.suffix == '.epub':
            text_content = self.extract_text_from_epub(file_path)
        
        if text_content:
            # Save processed text
            text_filename = file_path.stem + '.txt'
            text_path = self.processed_dir / text_filename
            
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(f"Source: {file_path.name}\n")
                f.write(f"Processed: {metadata['processed_at']}\n")
                f.write("=" * 80 + "\n\n")
                f.write(text_content)
            
            metadata['text_file'] = str(text_path.relative_to(self.base_dir))
            metadata['text_length'] = len(text_content)
            metadata['word_count'] = len(text_content.split())
            
            # Generate content hash
            metadata['content_hash'] = hashlib.sha256(text_content.encode()).hexdigest()
        
        return metadata
    
    def run(self):
        """Main execution: download and process all publications."""
        print("=" * 80)
        print("Sri Chaitanya Saraswat Math Publications Dataset Creator")
        print("=" * 80)
        
        all_links = []
        
        # Scrape all pages
        print("\n📚 Phase 1: Discovering publications...")
        for category, url in self.PAGES.items():
            base_url = '/'.join(url.split('/')[:3])  # Get base domain
            links = self.scrape_links(url, base_url)
            
            for link in links:
                link['category'] = category
                all_links.append(link)
        
        print(f"\n📊 Total files found: {len(all_links)}")
        
        # Download all files
        print("\n⬇️  Phase 2: Downloading publications...")
        downloaded_files = []
        
        for i, link_info in enumerate(all_links, 1):
            print(f"\n[{i}/{len(all_links)}]")
            
            # Determine destination directory
            category = link_info['category']
            if 'english_pdfs' in category:
                dest_dir = self.downloads_dir / "pdfs_english"
            elif 'english_epubs' in category:
                dest_dir = self.downloads_dir / "epubs_english"
            elif 'indian_lang' in category:
                dest_dir = self.downloads_dir / "pdfs_indian_languages"
            else:
                dest_dir = self.downloads_dir / "articles"
            
            dest_path = dest_dir / link_info['filename']
            
            # Skip if already downloaded
            if dest_path.exists():
                print(f"⏭️  Already exists: {dest_path.name}")
                downloaded_files.append(dest_path)
                continue
            
            # Download
            if self.download_file(link_info['url'], dest_path):
                downloaded_files.append(dest_path)
                time.sleep(1)  # Be polite to the server
        
        # Process all files
        print("\n📝 Phase 3: Extracting text from publications...")
        for i, file_path in enumerate(downloaded_files, 1):
            print(f"\n[{i}/{len(downloaded_files)}]")
            metadata = self.process_file(file_path)
            self.manifest['files'].append(metadata)
        
        # Generate statistics
        self.manifest['statistics'] = {
            'total_files': len(downloaded_files),
            'total_size_mb': sum(f.stat().st_size for f in downloaded_files) / (1024 * 1024),
            'file_types': {},
            'total_words': sum(m.get('word_count', 0) for m in self.manifest['files'])
        }
        
        for metadata in self.manifest['files']:
            file_type = metadata['file_type']
            self.manifest['statistics']['file_types'][file_type] = \
                self.manifest['statistics']['file_types'].get(file_type, 0) + 1
        
        # Save manifest
        manifest_path = self.metadata_dir / 'manifest.json'
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 80)
        print("✅ COMPLETE!")
        print("=" * 80)
        print(f"📁 Base directory: {self.base_dir}")
        print(f"📄 Total files: {self.manifest['statistics']['total_files']}")
        print(f"💾 Total size: {self.manifest['statistics']['total_size_mb']:.2f} MB")
        print(f"📝 Total words: {self.manifest['statistics']['total_words']:,}")
        print(f"📋 Manifest: {manifest_path}")
        print("\n🙏 Hare Krishna! Dataset ready for LLM training.")


def main():
    """Entry point."""
    downloader = SCSMathDownloader()
    downloader.run()


if __name__ == "__main__":
    main()
