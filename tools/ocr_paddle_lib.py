from paddleocr import PaddleOCRVL
from pathlib import Path
import time

def test_paddleocr_lib():
    image_path = "ocr_debug_page5.png"
    if not Path(image_path).exists():
        print("❌ Sample image not found")
        return

    print("🚀 Initializing PaddleOCRVL pipeline...")
    try:
        # PaddleOCRVL often downloads models on first init
        pipeline = PaddleOCRVL()
        
        print("🤖 Running OCR...")
        start_time = time.time()
        output = pipeline.predict(image_path)
        print(f"✅ OCR complete in {time.time() - start_time:.2f}s")
        
        # Process output
        # Based on docs, output is a list of results
        for i, res in enumerate(output):
            print(f"\n--- Result {i} ---")
            res.print()
            
    except Exception as e:
        print(f"❌ PaddleOCR Lib Error: {e}")

if __name__ == "__main__":
    test_paddleocr_lib()
