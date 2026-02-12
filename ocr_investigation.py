from pdf2image import convert_from_path
import pytesseract
from pathlib import Path
import json

def ocr_test():
    pdf_path = Path('entropy_samples/indian_lang_pdfs_0.pdf')
    if not pdf_path.exists():
        print("❌ Sample not found")
        return

    print(f"📸 Converting page 5 of {pdf_path.name} to image...")
    try:
        # Convert only page 5
        images = convert_from_path(pdf_path, first_page=5, last_page=5, dpi=300)
        
        if not images:
            print("❌ No images extracted")
            return
            
        img = images[0]
        output_img_path = Path('ocr_debug_page5.png')
        img.save(output_img_path)
        
        print("🤖 Running OCR (ben+eng)...")
        # Religious books often use mixed scripts
        text = pytesseract.image_to_string(img, lang='ben+eng')
        
        output_txt_path = Path('ocr_test_result.txt')
        output_txt_path.write_text(text, encoding='utf-8')
        
        print("\n📝 --- OCR Result Snippet ---")
        print(text[:1000])
        print("----------------------------\n")
        
    except Exception as e:
        print(f"❌ OCR Error: {e}")

if __name__ == "__main__":
    ocr_test()
