import os
import json
import math
import hashlib
from pathlib import Path
import pikepdf
from epub_meta import get_epub_metadata
import magic

class EntropyScanner:
    def __init__(self, library_dir='scsmath_library'):
        self.library_dir = Path(library_dir)
        self.report = {
            'metadata_stats': {},
            'clusters': {},
            'files': []
        }

    def calculate_entropy(self, file_path):
        with open(file_path, 'rb') as f:
            data = f.read()
        if not data: return 0
        entropy = 0
        for x in range(256):
            p_x = float(data.count(x))/len(data)
            if p_x > 0:
                entropy += - p_x * math.log(p_x, 2)
        return entropy

    def scan(self):
        print(f"🧐 Scanning library for entropy and metadata...")
        
        for file_path in self.library_dir.rglob('*'):
            if file_path.is_dir(): continue
            
            # Basic Info
            mime = magic.from_file(str(file_path), mime=True)
            ent = self.calculate_entropy(file_path)
            size = file_path.stat().st_size
            
            file_info = {
                'path': str(file_path),
                'filename': file_path.name,
                'category': file_path.parent.name,
                'mime': mime,
                'entropy': ent,
                'size_kb': size / 1024
            }
            
            # Deep Metadata
            if 'pdf' in mime:
                try:
                    with pikepdf.open(file_path) as pdf:
                        file_info['pdf_version'] = pdf.pdf_version
                        file_info['producer'] = str(pdf.docinfo.get('/Producer', 'unknown'))
                        file_info['creator'] = str(pdf.docinfo.get('/Creator', 'unknown'))
                        file_info['is_linearized'] = pdf.is_linearized
                        file_info['page_count'] = len(pdf.pages)
                except:
                    file_info['pdf_error'] = True
            elif 'epub' in mime or 'zip' in mime:
                try:
                    meta = get_epub_metadata(str(file_path))
                    file_info['title'] = meta.title
                    file_info['authors'] = meta.authors
                except:
                    file_info['epub_error'] = True
            
            self.report['files'].append(file_info)
            
            # Clustering logic: Group by Category + PDF Producer (if applicable)
            cluster_id = file_info['category']
            if 'pdf_version' in file_info:
                cluster_id += f"_{file_info['pdf_version']}_{file_info['producer'][:20]}"
            
            if cluster_id not in self.report['clusters']:
                self.report['clusters'][cluster_id] = []
            self.report['clusters'][cluster_id].append(file_info['filename'])

        # Final stats
        with open('bulk_entropy_report.json', 'w') as f:
            json.dump(self.report, f, indent=2)
        
        print(f"✨ Scan complete. Found {len(self.report['files'])} files across {len(self.report['clusters'])} clusters.")
        print(f"📊 Report saved to bulk_entropy_report.json")

if __name__ == "__main__":
    scanner = EntropyScanner()
    scanner.scan()
