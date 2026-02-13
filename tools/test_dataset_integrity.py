import os
from pathlib import Path
import json

def run_integrity_tests():
    dataset_dir = Path('mini_dataset')
    report_path = Path('mini_dataset_report.json')
    
    if not dataset_dir.exists():
        print("❌ CRITICAL: mini_dataset directory does not exist.")
        return

    with open(report_path, 'r') as f:
        report = json.load(f)

    print(f"🕵️ Testing {len(report)} dataset entries...")
    
    failures = 0
    for entry in report:
        fname = f"{entry['original']}.txt"
        file_path = dataset_dir / fname
        
        print(f"\n📄 File: {fname}")
        
        # Test 1: Existence
        if not file_path.exists():
            print("  ❌ FAIL: File not found on disk.")
            failures += 1
            continue
            
        content = file_path.read_text(encoding='utf-8').strip()
        
        # Test 2: Placeholder detection
        placeholders = ["[OCR REQUIRED", "[EPUB SANITISATION", "[SANITISED TEXT FOR"]
        is_placeholder = any(p in content for p in placeholders)
        
        # Test 3: Length check
        word_count = len(content.split())
        
        if len(content) == 0:
            print("  ❌ FAIL: File is completely empty.")
            failures += 1
        elif is_placeholder:
            print(f"  ❌ FAIL: File contains only a placeholder: '{content[:30]}...'")
            failures += 1
        elif word_count < 50:
            print(f"  ⚠️  WARNING: Very low word count ({word_count}). Check if extraction failed.")
        else:
            print(f"  ✅ PASS: {word_count} words found.")
            print(f"  Snippet: {content[:100].replace('\n', ' ')}...")

    print(f"\n📊 SUMMARY: {failures} failures found in {len(report)} files.")
    return failures == 0

if __name__ == "__main__":
    run_integrity_tests()
