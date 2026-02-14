import re
import os
import unicodedata
from pathlib import Path

class CanonicalNormalizer:
    def __init__(self):
        # 1. OCR Artifact Fixes (from EnglishSanitizer)
        self.ocr_fixes = [
            (r'çr\^', 'Srila'),
            (r'Ír\(', 'Sri'),
            (r'Maéh', 'Math'),
            (r'Maöh', 'Math'),
            (r'Gauråíga', 'Gauranga'),
            (r'Gaurå&ga', 'Gauranga'),
            (r'Ír\(la', 'Srila'),
            (r'Srilala', 'Srila'),
            (r'Vi!@upåd', 'Vishnupad'),
            (r'Rak!ak', 'Rakshak'),
            (r'Ír\(dhar', 'Sridhar'),
            (r'Ír\(man', 'Sriman'),
        ]

        # 2. Diacritic Standardization (from TextCleaner)
        self.diacritic_replacements = {
            r'\bKrishna\b': 'Kṛṣṇa',
            r'\bSrila\b': 'Śrīla',
            r'\bSri\b': 'Śrī',
            r'\bSrimad\b': 'Śrīmad',
            r'\bChaitanya\b': 'Caitanya',
            r'\bSaranagati\b': 'Śaraṇāgati',
            r'\bBhakti\b': 'Bhakti',
            r'\bVaishnava\b': 'Vaiṣṇava',
            r'\bMaharaj\b': 'Mahārāj',
        }

        # 3. Institutional Boilerplate Removal
        self.boilerplate_regex = [
            r'All glories to Sri Guru and Sri Gauranga',
            r'All Glory to Sri Sri Guru-Gauranga',
            r'Sri Chaitanya Saraswat Math',
            r'Kolerganj, (?:P\.O\.|Post Office:) Nabadwip,.*?(?:Pin \d+|West Bengal|India)',
            r'Website: http://www\.scsmath\.com',
            r'© All rights reserved by.*',
            r'Edited by:.*',
            r'Published by:.*',
            r'Assistant editor:.*',
            r'Founder-Acharya:.*',
            r'Sevaite-President-Acharya:.*',
            r'Printed in India.*',
            r'— \d+ —', # Page numbers
            r'—·  · — \d+', # Fancy page numbers
            r'www\..*\.org',
            r'http[s]?://\S+',
            r'Email: \S+',
            r'Mobile: \S+',
            r'Phone: \S+',
            r'Fax: \S+'
        ]

    def normalize_chars(self, text):
        """Fix OCR artifacts and control characters."""
        # Remove control characters except newline and tab
        text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'C' or ch in '\n\t')
        
        for pattern, replacement in self.ocr_fixes:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text

    def standardize_diacritics(self, text):
        """Standardize transliteration to include diacritics."""
        for pattern, replacement in self.diacritic_replacements.items():
            text = re.sub(pattern, replacement, text)
        return text

    def strip_boilerplate(self, text):
        """Remove institutional boilerplate and contact info."""
        for pattern in self.boilerplate_regex:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        lines = [line.strip() for line in text.split('\n')]
        return '\n'.join([line for line in lines if line])

    def clean(self, text):
        """Full normalization pipeline."""
        text = self.normalize_chars(text)
        text = self.strip_boilerplate(text)
        text = self.standardize_diacritics(text)
        return text.strip()

def process_directory(input_dir, output_dir):
    normalizer = CanonicalNormalizer()
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    files = list(input_path.glob("*.txt"))
    print(f"🧹 Found {len(files)} files to clean.")

    for file_path in files:
        print(f"  🧼 Processing {file_path.name}...")
        try:
            content = file_path.read_text(encoding='utf-8')
            cleaned_content = normalizer.clean(content)
            
            output_file = output_path / file_path.name
            output_file.write_text(cleaned_content, encoding='utf-8')
        except Exception as e:
            print(f"  ❌ Error processing {file_path.name}: {e}")

if __name__ == "__main__":
    process_directory("data/raw", "data/cleaned")
