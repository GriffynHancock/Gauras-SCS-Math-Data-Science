# Quick Start Guide

## For the Busy Cybersecurity Student 🔐

Since you're busy with cybersecurity studies in Melbourne, here's the absolute fastest way to get this done:

## Option 1: Fully Automated (Recommended)

```bash
# 1. Make the script executable
chmod +x setup_and_run.sh

# 2. Run it (handles everything)
./setup_and_run.sh

# 3. Go study for your cybersec exam! ☕
# Come back in 30-60 minutes
```

That's it! The script will:
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Download all publications (~150 files)
- ✅ Extract text from PDFs and EPUBs
- ✅ Generate manifest and metadata
- ✅ Create organized directory structure

## Option 2: Manual (If You Want Control)

```bash
# 1. Create virtual environment
python3.12 -m venv scsmath_env
source scsmath_env/bin/activate

# 2. Install dependencies
pip install requests beautifulsoup4 lxml PyPDF2 ebooklib

# 3. Run the downloader
python scsmath_data_processor.py

# 4. (Optional) Run analysis utilities
python dataset_utilities.py
```

## What You Get

After completion, you'll have:

```
scsmath_dataset/
├── downloads/              # All original PDFs and EPUBs (~2-3 GB)
│   ├── pdfs_english/       # ~50 English books
│   ├── epubs_english/      # ~15 EPUB versions
│   ├── pdfs_indian_languages/  # ~40 Bengali/Hindi/Oriya texts
│   └── articles/           # Miscellaneous articles
│
├── processed_text/         # Clean text files ready for training
│   ├── SearchForSriKrishna.txt
│   ├── LovingSearch.txt
│   └── ...
│
└── metadata/
    ├── manifest.json       # Complete index
    └── analysis_report.json  # Dataset statistics
```

## Using It for LLM Training

### Quick RAG Setup (Vector Database)

```python
# Install additional deps
pip install langchain chromadb sentence-transformers

# Create vector database (add to your script)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings

texts = []
for txt in Path('scsmath_dataset/processed_text').glob('*.txt'):
    texts.append(txt.read_text())

splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
chunks = splitter.split_documents(texts)

embeddings = HuggingFaceEmbeddings()
vectordb = Chroma.from_documents(chunks, embeddings)

# Now you have a queryable database of all teachings!
```

### Fine-tuning Prep

```bash
# Convert to training format
python dataset_utilities.py

# This creates: scsmath_dataset/training_instruction_format.jsonl
# Use this for fine-tuning Claude, GPT, Llama, etc.
```

## Estimated Times (M3 Mac Air, 100 Mbps)

- Download: 20-30 minutes
- Text extraction: 10-15 minutes  
- Total: ~45 minutes

## Troubleshooting

### "Permission denied"
```bash
chmod +x setup_and_run.sh
chmod +x scsmath_data_processor.py
```

### "Module not found"
```bash
# Make sure virtual environment is activated
source scsmath_env/bin/activate

# Reinstall
pip install -r requirements.txt
```

### Downloads failing
- Check internet connection
- The script has auto-retry logic
- Worst case: re-run the script (it skips existing files)

### PDFs not extracting text
Some old scanned PDFs might not have text. Options:
1. Keep the PDF (you have the original)
2. Use OCR: `pip install pytesseract pdf2image`
3. Many PDFs will extract fine - don't worry about a few failures

## After Completion

Send to your guru:
```bash
# Create summary report
python dataset_utilities.py

# Email them the statistics
cat scsmath_dataset/metadata/analysis_report.json
```

Tell them:
- ✅ Complete digital archive created
- ✅ All texts preserved and searchable
- ✅ Ready for AI training/RAG systems
- ✅ ~2 million words of teachings processed

## Git Workflow (For Your GitHub)

```bash
# Initialize git (if not already)
cd ~/path/to/project
git init

# Create .gitignore
cat > .gitignore << EOF
scsmath_env/
scsmath_dataset/downloads/
*.pyc
__pycache__/
.DS_Store
EOF

# Add files
git add scsmath_data_processor.py
git add dataset_utilities.py
git add README.md
git add requirements.txt
git add setup_and_run.sh
git add QUICKSTART.md

# Commit
git commit -m "Add SCS Math publications dataset creator"

# Push to GitHub
git remote add origin https://github.com/yourusername/scsmath-dataset.git
git push -u origin main
```

## Need Help?

1. Check README.md (full documentation)
2. Check the manifest.json (see what downloaded)
3. Debug with: `python -v scsmath_data_processor.py`

---

**Jay Guru! Jay Gauranga! 🙏**

*Now go ace those cybersecurity exams!*
