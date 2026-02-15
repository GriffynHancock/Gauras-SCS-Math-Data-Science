import os
import re
from pathlib import Path

class BookAuthorMapper:
    def __init__(self, attribution_file="book attribution.txt"):
        self.mapping = {}
        self._parse_file(attribution_file)

    def _parse_file(self, file_path):
        if not os.path.exists(file_path):
            print(f"⚠️ Warning: Attribution file {file_path} not found.")
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # The file seems to have a header: Book Link | BOOK TITLE | AUTHOR | PDF file SIZE
        # It's a bit messy, possibly tab-separated or just spaces from a table copy.
        
        for line in lines:
            if "BOOK TITLE" in line and "AUTHOR" in line:
                continue
            
            # Split by tabs first
            parts = line.strip().split('	')
            if len(parts) >= 3:
                title = parts[1].strip()
                author = parts[2].strip()
                self.mapping[self._normalize_title(title)] = author
            else:
                # Try fallback split if tabs aren't used correctly
                # Looking at the 'cat' output, it seems to have some tabs
                pass

        # Manual overrides/additions for filenames commonly used in scsmath_library
        self.manual_mapping = {
            "LovingSearchForTheLostServant": "Srila B.R. Sridhar Maharaj",
            "HeartandHalo": "Srila B.R. Sridhar Maharaj",
            "RevealedTruth": "Srila B.S. Govinda Maharaj",
            "SubjectiveEvolutionofConsciousness": "Srila B.R. Sridhar Maharaj",
            "SermonsoftheGuardianofDevotionVol1": "Srila B.R. Sridhar Maharaj",
            "SermonsoftheGuardianofDevotionVol2": "Srila B.R. Sridhar Maharaj",
            "SermonsoftheGuardianofDevotionVol3": "Srila B.R. Sridhar Maharaj",
            "SermonsoftheGuardianofDevotionVol4": "Srila B.R. Sridhar Maharaj",
            "InnerFulfilment": "Srila B.R. Sridhar Maharaj",
            "GoldenVolcanoofDivineLove": "Srila B.R. Sridhar Maharaj",
            "SriGuruandHisGrace": "Srila B.R. Sridhar Maharaj",
            "SearchForSriKrishna": "Srila B.R. Sridhar Maharaj",
            "HomeComfort": "Srila B.R. Sridhar Maharaj",
            "DivineGuidance": "Srila B.S. Govinda Maharaj",
            "AffectionateGuidance": "Srila B.S. Govinda Maharaj",
            "DignityoftheDivineServitor": "Srila B.S. Govinda Maharaj",
        }

    def _normalize_title(self, title):
        # Remove "en-" prefix, remove spaces, lower case for matching
        t = title.replace("en-", "").replace(" ", "").lower()
        # Remove common suffixes
        t = re.sub(r'\(.*?\)', '', t)
        t = t.replace("-", "").strip()
        return t

    def get_author(self, filename_or_title):
        # 1. Check manual mapping (high confidence)
        stem = Path(filename_or_title).stem
        normalized_stem = self._normalize_title(stem)
        
        for key, author in self.manual_mapping.items():
            if self._normalize_title(key) == normalized_stem:
                return author

        # 2. Check file-based mapping
        for title, author in self.mapping.items():
            if self._normalize_title(title) == normalized_stem:
                return author
        
        # 3. Fallback heuristics based on filename
        if "Sridhar" in filename_or_title:
            return "Srila B.R. Sridhar Maharaj"
        if "Govinda" in filename_or_title:
            return "Srila B.S. Govinda Maharaj"
        if "BhaktiVinod" in filename_or_title or "Saranagati" in filename_or_title:
            return "Srila Bhakti Vinod Thakur"

        return "Srila B.R. Sridhar Maharaj" # Defaulting to Sridhar Maharaj for this library

if __name__ == "__main__":
    mapper = BookAuthorMapper()
    print(f"Author for 'en-LovingSearchForTheLostServant': {mapper.get_author('en-LovingSearchForTheLostServant.txt')}")
    print(f"Author for 'en-RevealedTruth': {mapper.get_author('en-RevealedTruth.txt')}")
