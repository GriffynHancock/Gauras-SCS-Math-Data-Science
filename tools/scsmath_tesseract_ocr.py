import os
import time
import random
from pathlib import Path
from pdf2image import convert_from_path
import pytesseract
from dataset_utilities import TextCleaner
import pypdfium2 as pdfium

def run_tesseract(image, lang):
    # OEM 1: LSTM Engine Only
    # PSM 3: Fully automatic page segmentation, but no OSD. (Faster than PSM 1)
    custom_config = r'--oem 1 --psm 3'
    return pytesseract.image_to_string(image, lang=lang, config=custom_config)

def process_pdf_tesseract(pdf_path, output_dir, num_samples=None):
    pdf_path = Path(pdf_path)
    print(f"📖 Processing {pdf_path.name}...")
    
    pdf = pdfium.PdfDocument(str(pdf_path))
    total_pages = len(pdf)
    
    if num_samples:
        start_page = int(total_pages * 0.1)
        end_page = int(total_pages * 0.9)
        if start_page >= end_page:
            pages_to_process = [total_pages // 2]
        else:
            pages_to_process = sorted(random.sample(range(start_page, end_page), min(num_samples, end_page-start_page)))
    else:
        pages_to_process = range(total_pages)

    print(f"   Targeting {len(pages_to_process)} pages...")
    
    book_output = output_dir / pdf_path.stem
    book_output.mkdir(parents=True, exist_ok=True)
    
    for page_idx in pages_to_process:
        page_num = page_idx + 1
        
        # Convert page to image
        images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num, dpi=300)
        if not images:
            continue
        img = images[0]
        
        # 1. Detect Script (Quick pass)
        # We use a broad lang set for detection
        raw_detection = run_tesseract(img, "ben+hin+san")
        script = TextCleaner.detect_script(raw_detection)
        
        # 2. Select Optimized Setting
        if script == "Bengali":
            tess_lang = "ben" # ben is usually very strong in default Tesseract
            is_ben = True
        else:
            # For Devanagari, using san+hin often helps with the mixed 
            # religious/philosophical nature of these texts.
            tess_lang = "san+hin"
            is_ben = False
            
        print(f"   📄 Page {page_num}: Detected {script} -> Using '{tess_lang}'")
        
        # 3. Final OCR Pass
        text = run_tesseract(img, tess_lang)
        
        # 4. Clean and Save
        cleaned_text = TextCleaner.clean_text(text, is_bengali=is_ben)
        
        output_file = book_output / f"page_{page_num:03d}.txt"
        output_file.write_text(cleaned_text, encoding='utf-8')

def main():
    # Production directory for all OCR'd texts
    output_dir = Path("ocr_dataset")
    output_dir.mkdir(exist_ok=True)
    
    # For now, let's process the ones we've been testing
    target_pdfs = [
        "scsmath_library/indian_lang_pdfs/Rochanamrita.pdf",
        "scsmath_library/indian_lang_pdfs/KalyanaKalpaTaru.pdf",
        "scsmath_library/indian_lang_pdfs/ShashvataSukhaNiketana_Hindi.pdf"
    ]
    
    for pdf_str in target_pdfs:
        pdf_path = Path(pdf_str)
        if pdf_path.exists():
            # Process 5 random pages as a sanity check/sample
            process_pdf_tesseract(pdf_path, output_dir, num_samples=5)
        else:
            print(f"❌ {pdf_str} not found")

if __name__ == "__main__":
    main()
