import os
from pathlib import Path
import shutil
import random

def create_micro_dataset():
    source_dir = Path("data/cleaned")
    target_dir = Path("data/micro_test/raw")
    
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📂 Creating micro dataset in {target_dir}...")
    
    files = list(source_dir.glob("*.txt"))
    if not files:
        print(f"❌ No text files found in {source_dir}")
        return

    processed_count = 0
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            if total_lines == 0:
                print(f"⚠️ Empty file: {file_path.name}")
                continue
                
            # extract 400 lines from the middle (approx 10 pages)
            chunk_size = 400
            start_index = max(0, (total_lines - chunk_size) // 2)
            end_index = min(total_lines, start_index + chunk_size)
            
            extracted_lines = lines[start_index:end_index]
            
            # Add a header indicating where this came from
            header = f"--- EXTRACTED FROM {file_path.name} (Lines {start_index}-{end_index}) ---\n\n"
            content = header + "".join(extracted_lines)
            
            target_path = target_dir / file_path.name
            with open(target_path, 'w', encoding='utf-8') as f_out:
                f_out.write(content)
            
            processed_count += 1
            # print(f"  ✅ Processed {file_path.name} ({len(extracted_lines)} lines)")
            
        except Exception as e:
            print(f"❌ Error processing {file_path.name}: {e}")

    print(f"🎉 Created micro dataset with {processed_count} files.")

if __name__ == "__main__":
    create_micro_dataset()
