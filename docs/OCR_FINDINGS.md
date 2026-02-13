# OCR Investigation Findings

## Summary
The Indian language publications (Bengali/Hindi) are stored as image-scanned PDFs. Standard text extraction fails, but high-resolution OCR is 100% viable.

## Technical Details
- **Source Format:** Image-only PDF (No embedded fonts).
- **OCR Engine:** Tesseract 5.5.2.
- **Language Data:** `ben` (Bengali) and `hin` (Hindi) verified.
- **Accuracy:** Extremely High. Tested on `indian_lang_pdfs_0.pdf` (page 5).

### Sample Extraction (Bengali)
**Raw Output:**
```
বহিগর্ভ বিপ্রলন্ত লীলার সমাহার
প্রবক্তা
ও বিষুপাদ
পরমহংসকুলবরেণ্য জগদ্গুরু
বিশ্বব্যাপী ভ্রীচৈতন্য-সারস্বত মঠাদি প্রতিষ্ঠানের প্রতিষ্ঠাতা-
সভাপতি-আচার্ধ্য
```

**Translation/Analysis:**
- "A collection of Bahirgarbha Vipralambha Leela"
- "Speaker: Om Vishnupad"
- "Jagadguru, the best of the Paramahamsas"
- "Founder-President-Acharya of the worldwide Sri Chaitanya Saraswat Math"

## Difficulty Score: 7/10
While the OCR is accurate, the pipeline will be slower than the English PDF pipeline because:
1. Each page must be rendered to a 300 DPI image.
2. Tesseract processing time is significantly higher than PyPDF2.
3. Multi-script handling (Bengali + Sanskrit + English) requires careful language tagging.

## Recommendation
Proceed with a batch-processing OCR worker for all Indian language PDFs. Use `pdf2image` for rasterization and `pytesseract` for extraction.
