# Gaura's Sri Chaitanya Saraswat Math Data Science Plan

This document tracks the methodical progress of the SCS Math publication processing pipeline. Each step must be verified by reading back the code and testing on samples before proceeding.

## Phase 1: Cleaning & Sanitization (English)
- [ ] **Boilerplate Removal Logic (English PDFs)**
  - Goal: Remove "Sri Chaitanya Saraswat Math", addresses, copyright notices, and page numbers that pollute the LLM context.
  - Method: Multi-stage regex and structural analysis.
- [ ] **EPUB Extraction Refinement**
  - Goal: Clean HTML artifacts from EPUB items and preserve semantic flow.
- [ ] **Verification**
  - [ ] Test on 3 random English PDF samples.
  - [ ] Test on 3 random English EPUB samples.
  - [ ] Compare "Pre" and "Post" sanitization entropy.

## Phase 2: OCR Investigation (Indian Languages)
- [ ] **Sampling & Extraction**
  - [ ] Pick 3 random Indian Language PDFs (Bengali/Hindi).
  - [ ] Convert sample pages to high-res images.
- [ ] **OCR Execution**
  - [ ] Test Tesseract (Standard).
  - [ ] Test LLM-based OCR (via vision model if available).
- [ ] **Translation & Coherence Check**
  - [ ] Translate extracted text to English.
  - [ ] Evaluate if the result is spiritually/philosophically coherent.
- [ ] **Documentation**
  - [ ] Write `OCR_FINDINGS.md` summarizing viability.

## Phase 3: Bulk Acquisition & Entropy Grouping
- [ ] **Bulk Download**
  - [ ] Download all 184+ sources discovered in Phase 1.
- [ ] **Data/Metadata Clustering**
  - [ ] Scan entire library for PDF Version, Creation Date, Producer Tool (e.g., Acrobat vs Distiller).
  - [ ] Group texts based on metadata similarity and raw binary entropy.
- [ ] **GitHub Initialization**
  - [ ] Create repository: `Gaura's Sri Chaitanya Saraswath Math Data Science`.
  - [ ] Push codebase and initial reports.

## Phase 4: Specialized Sanitization Tooling (Phase 0)
- [ ] **Group-Specific Sanitizers**
  - [ ] Write targeted scripts for each cluster identified in Phase 3.
- [ ] **Mini-Dataset Generation**
  - [ ] Process 3 random texts from each group.
  - [ ] Generate analysis report on sanitized text (Word counts, N-grams).

## Phase 5: Semantic Analysis (Phase 0.1)
- [ ] **Embeddings Generation**
  - [ ] Embed the sanitized data using a suitable model.
- [ ] **Cluster Analysis**
  - [ ] Identify clusters of related words and philosophical concepts.

---
*Note: Every tool developed must be run on a sample of 3 before being applied to a group.*
