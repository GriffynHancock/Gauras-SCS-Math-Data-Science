#!/usr/bin/env python3
"""
Advanced Dataset Processing Utilities
======================================
Additional tools for cleaning, analyzing, and preparing the SCS Math dataset.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Set
from collections import Counter
import unicodedata


class TextCleaner:
    """Clean and normalize extracted text."""
    
    @staticmethod
    def remove_headers_footers(text: str) -> str:
        """Remove common headers/footers from book pages."""
        lines = text.split('\n')
        cleaned = []
        
        for line in lines:
            # Skip page numbers
            if re.match(r'^\s*\d+\s*$', line):
                continue
            # Skip common headers
            if re.search(r'(Sri Chaitanya Saraswat Math|www\.scsmath|Page \d+)', line, re.I):
                continue
            cleaned.append(line)
        
        return '\n'.join(cleaned)
    
    @staticmethod
    def normalize_sanskrit(text: str) -> str:
        """Normalize Sanskrit transliteration."""
        # Common variations to standardize
        replacements = {
            'Krishna': 'Kṛṣṇa',
            'Srila': 'Śrīla',
            'Sri': 'Śrī',
            'Srimad': 'Śrīmad',
            'Chaitanya': 'Caitanya',
        }
        
        # You can expand this based on your tradition's preferences
        result = text
        for old, new in replacements.items():
            result = re.sub(rf'\b{old}\b', new, result)
        
        return result
    
    @staticmethod
    def fix_common_ocr_errors(text: str) -> str:
        """Fix common OCR mistakes in older PDFs."""
        fixes = {
            r'\bl\b': 'I',  # lowercase L misread as I
            r'\bO\b': '0',  # O misread as zero
            'tbe': 'the',
            'sbould': 'should',
            'witb': 'with',
        }
        
        result = text
        for pattern, replacement in fixes.items():
            result = re.sub(pattern, replacement, result)
        
        return result
    
    @staticmethod
    def clean_text(text: str, 
                   remove_headers: bool = True,
                   normalize_devanagari: bool = False,
                   fix_ocr: bool = True) -> str:
        """Comprehensive text cleaning pipeline."""
        
        # Remove control characters
        text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'C' or ch in '\n\t')
        
        # Fix OCR errors
        if fix_ocr:
            text = TextCleaner.fix_common_ocr_errors(text)
        
        # Remove headers/footers
        if remove_headers:
            text = TextCleaner.remove_headers_footers(text)
        
        # Normalize Sanskrit if requested
        if normalize_devanagari:
            text = TextCleaner.normalize_sanskrit(text)
        
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        return text.strip()


class DatasetAnalyzer:
    """Analyze the dataset for quality and statistics."""
    
    def __init__(self, manifest_path: str):
        with open(manifest_path) as f:
            self.manifest = json.load(f)
    
    def analyze_vocabulary(self, min_frequency: int = 10) -> Dict[str, int]:
        """Extract vocabulary with frequency counts."""
        vocab = Counter()
        
        for file_info in self.manifest['files']:
            if 'text_file' not in file_info:
                continue
                
            text_path = Path(file_info['text_file'])
            if not text_path.exists():
                continue
                
            with open(text_path, encoding='utf-8') as f:
                text = f.read().lower()
                words = re.findall(r'\b\w+\b', text)
                vocab.update(words)
        
        # Filter by minimum frequency
        return {word: count for word, count in vocab.items() if count >= min_frequency}
    
    def find_duplicates(self) -> List[tuple]:
        """Find potential duplicate content."""
        seen_hashes = {}
        duplicates = []
        
        for file_info in self.manifest['files']:
            if 'content_hash' in file_info:
                h = file_info['content_hash']
                if h in seen_hashes:
                    duplicates.append((seen_hashes[h], file_info['filename']))
                else:
                    seen_hashes[h] = file_info['filename']
        
        return duplicates
    
    def generate_report(self, output_path: str):
        """Generate comprehensive dataset report."""
        report = {
            'summary': self.manifest['statistics'],
            'duplicates': self.find_duplicates(),
            'vocabulary_size': len(self.analyze_vocabulary(min_frequency=5)),
            'files_by_author': self._count_by_author(),
            'language_distribution': self._count_by_language(),
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Report saved to: {output_path}")
        return report
    
    def _count_by_author(self) -> Dict[str, int]:
        """Count files by author (if metadata available)."""
        authors = Counter()
        
        for file_info in self.manifest['files']:
            # Try to extract author from filename or metadata
            filename = file_info['filename']
            if 'Sridhar' in filename or 'SGuru' in filename:
                authors['Srila B.R. Sridhar Maharaj'] += 1
            elif 'Govinda' in filename or 'SGov' in filename:
                authors['Srila B.S. Govinda Maharaj'] += 1
            elif 'Bhaktivinod' in filename or 'BhaktiVinod' in filename:
                authors['Srila Bhakti Vinod Thakur'] += 1
            else:
                authors['Other/Unknown'] += 1
        
        return dict(authors)
    
    def _count_by_language(self) -> Dict[str, int]:
        """Count files by language."""
        languages = Counter()
        
        for file_info in self.manifest['files']:
            category = file_info.get('category', '')
            if 'english' in category:
                languages['English'] += 1
            elif 'indian_lang' in category:
                # Try to determine specific language
                filename = file_info['filename'].lower()
                if any(x in filename for x in ['bengali', 'bangla']):
                    languages['Bengali'] += 1
                elif 'hindi' in filename:
                    languages['Hindi'] += 1
                elif 'oriya' in filename or 'oriyan' in filename:
                    languages['Oriya'] += 1
                else:
                    languages['Indian Language (Unknown)'] += 1
            else:
                languages['Unknown'] += 1
        
        return dict(languages)


class TrainingDataPreparer:
    """Prepare data for various LLM training formats."""
    
    @staticmethod
    def create_instruction_dataset(
        manifest_path: str,
        output_path: str,
        max_length: int = 2048
    ):
        """Create instruction-following dataset format."""
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        instructions = []
        
        for file_info in manifest['files']:
            if 'text_file' not in file_info:
                continue
            
            text_path = Path(file_info['text_file'])
            if not text_path.exists():
                continue
            
            with open(text_path, encoding='utf-8') as f:
                full_text = f.read()
            
            # Split into chunks
            chunks = TrainingDataPreparer._split_into_chunks(full_text, max_length)
            
            for i, chunk in enumerate(chunks):
                # Create instruction-response pairs
                instruction_entry = {
                    'instruction': f"Explain the following excerpt from {file_info['filename']}:",
                    'input': chunk[:max_length // 2],  # First half as context
                    'output': chunk[max_length // 2:],  # Second half as response
                    'metadata': {
                        'source': file_info['filename'],
                        'chunk': i,
                        'total_chunks': len(chunks)
                    }
                }
                instructions.append(instruction_entry)
        
        # Save as JSONL
        with open(output_path, 'w', encoding='utf-8') as f:
            for entry in instructions:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        print(f"✅ Created {len(instructions)} instruction examples")
        print(f"📝 Saved to: {output_path}")
    
    @staticmethod
    def create_qa_pairs(manifest_path: str, output_path: str):
        """Create Q&A pairs for training (requires manual curation)."""
        # This is a template - you'd need to manually create Q&A pairs
        # or use an LLM to generate them
        
        qa_template = []
        
        # Example structure:
        example_qa = {
            'question': 'What is the nature of the soul according to Srila Sridhar Maharaj?',
            'answer': '[Extract from text]',
            'source': 'Search for Sri Krishna',
            'chapter': 'Chapter 2'
        }
        
        print("⚠️  Q&A pair generation requires manual curation or LLM assistance")
        print("Template structure created at:", output_path)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([example_qa], f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def _split_into_chunks(text: str, max_length: int) -> List[str]:
        """Split text into chunks respecting sentence boundaries."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence.split())
            
            if current_length + sentence_length > max_length:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks


def main():
    """Example usage of utilities."""
    
    print("SCS Math Dataset Utilities")
    print("=" * 80)
    
    # Analyze dataset
    print("\n📊 Analyzing dataset...")
    analyzer = DatasetAnalyzer('scsmath_dataset/metadata/manifest.json')
    report = analyzer.generate_report('scsmath_dataset/metadata/analysis_report.json')
    
    print(f"\n📈 Dataset Statistics:")
    print(f"  Total Files: {report['summary']['total_files']}")
    print(f"  Total Words: {report['summary']['total_words']:,}")
    print(f"  Vocabulary Size: {report['vocabulary_size']:,}")
    print(f"\n📚 Files by Author:")
    for author, count in report['files_by_author'].items():
        print(f"  {author}: {count}")
    
    # Prepare training data
    print("\n🔧 Preparing training data formats...")
    TrainingDataPreparer.create_instruction_dataset(
        'scsmath_dataset/metadata/manifest.json',
        'scsmath_dataset/training_instruction_format.jsonl'
    )
    
    print("\n✅ All utilities complete!")


if __name__ == "__main__":
    main()
