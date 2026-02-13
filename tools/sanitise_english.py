import re
import json
from pathlib import Path

class EnglishSanitizer:
    def __init__(self):
        # Patterns to normalize common diacritic artifacts found in extraction
        self.normalizations = [
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
            (r'acharya', 'acharya'),
            (r'acharyya', 'acharya'),
        ]

        # Patterns for boilerplate removal
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
        ]

    def normalize(self, text):
        for pattern, replacement in self.normalizations:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text

    def strip_boilerplate(self, text):
        # Remove TOC: Match 'Contents' and everything until a line that looks like the start of a chapter
        # but NOT if that chapter start is clearly part of the TOC (e.g. followed by dots or page numbers)
        # This is hard. Let's try to match 'Contents' up to the first 'Chapter 1' or 'Section 1' that is NOT in the TOC.
        # Actually, let's just remove the word 'Contents' and specific known front-matter for now to be safe.
        
        # Surgical removal of specific sections if they appear at the very end
        lines = text.split('\n')
        final_lines = []
        skip_to_end = False
        for i, line in enumerate(lines):
            # If we are near the end and see these, stop
            if i > len(lines) * 0.8:
                if re.match(r'^(Book List|Addresses|Appendix)', line, re.I):
                    skip_to_end = True
            if not skip_to_end:
                final_lines.append(line)
        
        text = '\n'.join(final_lines)

        for pattern in self.boilerplate_regex:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove empty lines and excessive whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)

    def sanitise(self, text):
        text = self.normalize(text)
        text = self.strip_boilerplate(text)
        return text

def test_sanitizer():
    sanitizer = EnglishSanitizer()
    samples_dir = Path('homogeneity_test')
    output_dir = Path('sanitised_test')
    output_dir.mkdir(exist_ok=True)

    for i in range(3):
        input_path = samples_dir / f"english_pdfs_{i}.txt"
        if input_path.exists():
            print(f"🧼 Sanitising {input_path.name}...")
            raw_text = input_path.read_text(encoding='utf-8')
            clean_text = sanitizer.sanitise(raw_text)
            
            output_path = output_dir / f"clean_english_pdfs_{i}.txt"
            output_path.write_text(clean_text, encoding='utf-8')
            
            # Basic metric: Reduction in size
            reduction = (1 - len(clean_text) / len(raw_text)) * 100
            print(f"  ✅ Done. Size reduction: {reduction:.2f}%")

if __name__ == "__main__":
    test_sanitizer()
