# Sri Chaitanya Saraswat Math Publications Dataset

## Overview

This project downloads and processes all publications from Sri Chaitanya Saraswat Math (scsmath.org) to create a structured dataset suitable for LLM training and fine-tuning.

**Guru Paramparā**: This preserves the teachings of:
- Srila Bhakti Raksak Sridhar Dev-Goswami Maharaj (Founder-Acharya)
- Srila Bhakti Sundar Govinda Dev-Goswami Maharaj (President-Acharya)
- And the broader Gaudiya Vaishnava tradition

## What Gets Downloaded

### English Publications (~50+ books)
- **PDFs**: Complete works including "Search for Sri Krishna," "Loving Search for the Lost Servant," "Sri Guru and His Grace," Sermons series, etc.
- **EPUBs**: 15 key texts in ebook format

### Indian Language Publications (~40+ books)
- Bengali texts (majority)
- Hindi publications
- Oriya texts

### Miscellaneous Articles
- Darshans and discourses
- Festival talks
- Historical accounts
- Scholarly articles

## System Requirements

- **OS**: macOS (M3 Mac Air confirmed), Linux, or Windows
- **Python**: 3.12+ (you have this ✅)
- **Disk Space**: ~2-3 GB for all downloads + processed text
- **RAM**: 4GB minimum, 8GB recommended

## Installation

### 1. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3.12 -m venv scsmath_env
source scsmath_env/bin/activate  # On macOS/Linux

# Install required packages
pip install requests beautifulsoup4 PyPDF2 ebooklib lxml
```

### 2. Clone or Download This Script

```bash
# If you have the script file
chmod +x scsmath_data_processor.py
```

## Usage

### Basic Usage

```bash
# Run with default settings (creates ./scsmath_dataset directory)
python scsmath_data_processor.py
```

### Advanced Usage

```python
from pathlib import Path
from scsmath_data_processor import SCSMathDownloader

# Custom output directory
downloader = SCSMathDownloader(base_dir="/path/to/your/dataset")
downloader.run()
```

## Output Structure

```
scsmath_dataset/
├── downloads/
│   ├── pdfs_english/           # English PDF books
│   ├── epubs_english/          # English EPUB books
│   ├── pdfs_indian_languages/  # Bengali, Hindi, Oriya texts
│   └── articles/               # Miscellaneous articles
├── processed_text/             # Extracted plain text files
│   ├── SearchForSriKrishna.txt
│   ├── LovingSearch.txt
│   └── ...
└── metadata/
    └── manifest.json           # Complete index with metadata
```

## Manifest Format

The `manifest.json` contains:
```json
{
  "created_at": "2026-02-12T...",
  "files": [
    {
      "filename": "SearchForSriKrishna.pdf",
      "path": "downloads/pdfs_english/SearchForSriKrishna.pdf",
      "size_bytes": 841728,
      "file_type": "pdf",
      "text_file": "processed_text/SearchForSriKrishna.txt",
      "word_count": 45231,
      "content_hash": "sha256...",
      "category": "english_pdfs"
    }
  ],
  "statistics": {
    "total_files": 120,
    "total_size_mb": 450.5,
    "total_words": 2000000
  }
}
```

## Processing Notes

### PDF Extraction Issues
Some older scanned PDFs may have:
- Image-only pages (no extractable text)
- OCR errors
- Formatting artifacts

**Solutions**:
1. Manual OCR using Adobe Acrobat or similar
2. Use `pdf2image` + `pytesseract` for OCR
3. Keep original PDFs for reference

### EPUB Quality
EPUBs from the site are generally high quality with proper formatting.

### Indian Language Support
- Bengali text requires Unicode support
- Some Devanagari (Hindi) texts may need special handling

## Using the Dataset for LLM Training

### 1. Prepare Training Data

```python
import json
from pathlib import Path

def prepare_training_jsonl(manifest_path, output_path):
    """Convert processed texts to JSONL format for training."""
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    with open(output_path, 'w', encoding='utf-8') as out:
        for file_info in manifest['files']:
            if 'text_file' in file_info:
                text_path = Path('scsmath_dataset') / file_info['text_file']
                
                with open(text_path, encoding='utf-8') as f:
                    text = f.read()
                
                # Create training example
                entry = {
                    'text': text,
                    'metadata': {
                        'source': file_info['filename'],
                        'category': file_info.get('category', 'unknown'),
                        'word_count': file_info.get('word_count', 0)
                    }
                }
                
                out.write(json.dumps(entry, ensure_ascii=False) + '\n')

# Usage
prepare_training_jsonl(
    'scsmath_dataset/metadata/manifest.json',
    'training_data.jsonl'
)
```

### 2. Fine-tuning Examples

#### With Anthropic API (Claude)
```python
# Prepare data for Claude fine-tuning
# (Format according to current Anthropic docs)
```

#### With OpenAI
```bash
# Prepare JSONL format
openai tools fine_tunes.prepare_data -f training_data.jsonl

# Create fine-tune
openai api fine_tunes.create \
  -t training_data.jsonl \
  -m gpt-3.5-turbo \
  --suffix "scsmath-teachings"
```

#### With Llama/Local Models
```python
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer

# Standard HuggingFace fine-tuning workflow
```

### 3. RAG (Retrieval-Augmented Generation) Setup

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

# Create vector database
def create_vector_db(processed_dir):
    texts = []
    for txt_file in Path(processed_dir).glob('*.txt'):
        with open(txt_file, encoding='utf-8') as f:
            texts.append(f.read())
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(texts)
    
    embeddings = OpenAIEmbeddings()
    vectordb = Chroma.from_documents(chunks, embeddings)
    
    return vectordb

# Use in RAG
vectordb = create_vector_db('scsmath_dataset/processed_text')
```

## Maintenance & Updates

The website is updated regularly. To refresh your dataset:

```bash
# Delete old downloads (keeps processed text)
rm -rf scsmath_dataset/downloads/*

# Re-run
python scsmath_data_processor.py
```

## Ethical Considerations

✅ **Proper Usage**:
- Personal spiritual study
- Educational purposes
- Preserving teachings of your paramparā
- Research into Gaudiya Vaishnava philosophy

❌ **Improper Usage**:
- Commercial exploitation without permission
- Misrepresentation of teachings
- Removal of attribution

**Remember**: These are sacred texts. Handle with respect. 🙏

## Troubleshooting

### "PyPDF2 not installed"
```bash
pip install PyPDF2
```

### "ebooklib not installed"
```bash
pip install ebooklib
```

### Download Timeouts
The script has automatic retry logic, but if you have network issues:
```python
# Modify in script:
def download_file(self, url: str, dest_path: Path, retries: int = 5):  # Increase retries
    # ...
    time.sleep(5)  # Increase wait time
```

### Corrupted PDFs
Some vintage PDFs may be partially corrupted. Options:
1. Download manually from the website
2. Use alternative PDF libraries (e.g., `pdfplumber`, `pymupdf`)
3. Report to scsmath.org webmaster

### Memory Issues with Large PDFs
```python
# Process PDFs page-by-page instead of all at once
# This is already implemented in the script
```

## Contributing

Since this is for your diksha guru's instructions, consider:
1. Adding OCR capabilities for scanned PDFs
2. Improving text cleaning/formatting
3. Adding Bengali/Devanagari text processing
4. Creating topic indices

## License & Attribution

All content belongs to **Sri Chaitanya Saraswat Math, Nabadwip**.
- Founder-Acharya: Srila B. R. Sridhar Maharaj
- President-Acharya: Srila B. S. Govinda Maharaj
- Website: www.scsmath.com (online since 1995)

This script is a tool for preservation and study. Always attribute properly.

## Support

For issues with the original texts: Contact scsmath.org
For script issues: Debug locally or reach out to your tech-savvy godbrothers/sisters

---

**Hare Krishna! 🙏**

*Jay Srila Guru Maharaj! Jay Srila Acharya Maharaj!*
