import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
from datetime import datetime
import time

class SourceDiscoverer:
    PAGES = {
        'english_pdfs': 'https://scsmath.org/publications/publications-pdfs.html',
        'english_epubs': 'https://scsmath.org/publications/publications-epubs.html',
        'indian_lang_pdfs': 'https://scsmath.org/publications/publications-IndianLanguage-pdfs.html',
        'misc_articles': 'https://scsmath.com/docs/text_archive.html'
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.index = {
            'metadata': {
                'discovery_date': datetime.now().isoformat(),
                'total_sources': 0
            },
            'sources': []
        }

    def discover(self):
        for category, url in self.PAGES.items():
            print(f"🔍 Exploring {category} at {url}...")
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                base_domain = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                
                count = 0
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(url, href)
                    
                    # Determine if it's a file or an article link
                    file_ext = Path(urlparse(full_url).path).suffix.lower()
                    
                    is_valid = False
                    source_type = 'unknown'
                    
                    if file_ext in ['.pdf', '.epub']:
                        is_valid = True
                        source_type = file_ext[1:]
                    elif category == 'misc_articles' and (href.endswith('.html') or href.endswith('.htm')):
                        # Articles are typically HTML pages
                        if 'text_archive' not in href and 'index.html' not in href:
                            is_valid = True
                            source_type = 'html_article'

                    if is_valid:
                        title = link.get_text(strip=True)
                        if not title or len(title) < 3:
                            # Contextual title search
                            parent = link.find_parent(['td', 'li', 'p'])
                            if parent:
                                title = parent.get_text(strip=True)[:200]
                        
                        self.index['sources'].append({
                            'category': category,
                            'type': source_type,
                            'title': title,
                            'url': full_url,
                            'discovered_at': datetime.now().isoformat()
                        })
                        count += 1
                
                print(f"✅ Found {count} sources in {category}")
                time.sleep(1)
            except Exception as e:
                print(f"❌ Error exploring {url}: {e}")

        self.index['metadata']['total_sources'] = len(self.index['sources'])
        
        with open('source_index.json', 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)
        print(f"\n✨ Discovery complete. {len(self.index['sources'])} sources saved to source_index.json")

if __name__ == "__main__":
    discoverer = SourceDiscoverer()
    discoverer.discover()
