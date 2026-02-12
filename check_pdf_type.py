import pikepdf
from pathlib import Path
import json

def check_indian_pdfs():
    samples_dir = Path('entropy_samples')
    results = {}
    
    for i in range(3):
        file_path = samples_dir / f"indian_lang_pdfs_{i}.pdf"
        if not file_path.exists(): continue
        
        print(f"🧐 Checking {file_path.name}...")
        try:
            with pikepdf.open(file_path) as pdf:
                has_fonts = False
                for page in pdf.pages[:5]:
                    if hasattr(page, 'Resources') and '/Font' in page.Resources:
                        has_fonts = True
                        break
                
                results[file_path.name] = {
                    "has_fonts": has_fonts,
                    "page_count": len(pdf.pages),
                    "producer": str(pdf.docinfo.get("/Producer", "Unknown")),
                    "creator": str(pdf.docinfo.get("/Creator", "Unknown")),
                    "is_linearized": pdf.is_linearized
                }
                print(f"  Result: {'Has Fonts (May be legacy encoding)' if has_fonts else 'No Fonts (Likely image-scan)'}")
        except Exception as e:
            results[file_path.name] = {"error": str(e)}
            print(f"  ❌ Error: {e}")
            
    with Path('indian_pdf_analysis.json').open('w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    check_indian_pdfs()
