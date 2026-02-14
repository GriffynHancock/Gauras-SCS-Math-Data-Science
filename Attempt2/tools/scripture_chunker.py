import re
from pathlib import Path

class ScriptureChunker:
    @staticmethod
    def is_scripture(file_path):
        scriptures = [
            "BrahmaSamhita",
            "Bhagavad-gītā",
            "Prapanna-jīvanāmṛtam",
            "Prema-vivarta"
        ]
        return any(s in str(file_path) for s in scriptures)

    @staticmethod
    def get_first_transliterated_line(text):
        """Finds the first line that looks like transliteration (IAST)."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        skip_patterns = ["uvācha", "uvacha", "Chapter", "Section", "Summary", "darśana", "darshana"]
        
        for line in lines:
            # Skip Sanskrit/Devanagari
            if any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in line):
                continue
            # Skip known labels
            if any(p.lower() in line.lower() for p in skip_patterns):
                continue
            # Skip verse number labels at start of translation
            if re.match(r'^\d+ ', line):
                continue
            # Transliteration usually has diacritics (ord > 127) or is mixed case (not all caps)
            if any(ord(c) > 127 for c in line) or (not line.isupper() and len(line) > 10):
                return line
        
        return lines[0] if lines else ""

    @staticmethod
    def split_into_normal_chunks(text, max_chars=2000):
        """Splits long text into roughly equal chunks by paragraph."""
        if len(text) <= max_chars:
            return [text]
        
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []
        current_len = 0
        
        for p in paragraphs:
            if current_len + len(p) > max_chars and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [p]
                current_len = len(p)
            else:
                current_chunk.append(p)
                current_len += len(p) + 2
                
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
        return chunks

    @staticmethod
    def chunk_bhagavad_gita(text, book_id):
        chunks = []
        marker_pattern = re.compile(r'\s+\[(\d+(?:–\d+)?)\]')
        parts = marker_pattern.split(text)
        
        verse_data = {}
        for i in range(1, len(parts), 2):
            v_num = parts[i]
            if v_num not in verse_data:
                verse_data[v_num] = {"before_marker": parts[i-1], "after_marker_blocks": []}
            verse_data[v_num]["after_marker_blocks"].append(parts[i+1])
            
        for v_num, data in verse_data.items():
            verse_text_raw = data["before_marker"].strip()
            all_blocks = data["after_marker_blocks"]
            last_block = all_blocks[-1]
            intermediate_blocks = all_blocks[:-1]
            
            cb_parts = verse_text_raw.split('\n\n')
            verse_parts_only = []
            for j in range(len(cb_parts)-1, -1, -1):
                p = cb_parts[j].strip()
                if not p: continue
                if re.match(r'^\d+ ', p) or p.lower() in ["commentary", "purport"]:
                    break
                verse_parts_only.insert(0, p)
            
            clean_verse_text = "\n\n".join(verse_parts_only)
            
            # Group Sanskrit and Transliteration (including word-for-word)
            full_sloka_text = clean_verse_text
            for block in intermediate_blocks:
                full_sloka_text += f" [{v_num}]\n\n" + block.strip()
                
            first_line_translit = ScriptureChunker.get_first_transliterated_line(full_sloka_text)
            
            # Extract translation and commentary
            ca_parts = last_block.split('\n\n')
            trans_comm_parts = []
            for p in ca_parts:
                p_strip = p.strip()
                if not p_strip: continue
                if not re.match(r'^\d+ ', p_strip) and \
                   not p_strip.lower().startswith("commentary") and \
                   any(ord(c) > 127 for c in p_strip):
                    break
                trans_comm_parts.append(p_strip)
                
            full_trans_comm = "\n\n".join(trans_comm_parts)
            tc_split = re.split(r'\nCommentary\n', full_trans_comm, flags=re.IGNORECASE)
            translation = tc_split[0].strip()
            commentary_raw = tc_split[1].strip() if len(tc_split) > 1 else None
            
            # MANDATE: Sanskrit-Transliteration-Translation always together
            combined_vtt = f"{full_sloka_text} [{v_num}]\n\n{translation}"
            chunks.append({
                "type": "verse+translation",
                "text": combined_vtt,
                "verse_num": v_num,
                "first_line_sloka": first_line_translit
            })
            
            # Purports in "normal chunks"
            if commentary_raw:
                comm_chunks = ScriptureChunker.split_into_normal_chunks(commentary_raw)
                for sub_i, comm_text in enumerate(comm_chunks):
                    chunks.append({
                        "type": "commentary",
                        "text": f"Commentary on Verse {v_num} (Part {sub_i+1}):\n\n{comm_text}",
                        "verse_num": v_num,
                        "first_line_sloka": first_line_translit
                    })
                
        return chunks

    @staticmethod
    def chunk_brahma_samhita(text, book_id):
        chunks = []
        sections = re.split(r'\nVerse (\d+)\n', text)
        for i in range(1, len(sections), 2):
            verse_num = sections[i]
            verse_content = sections[i+1]
            v_parts = re.split(r'\nTranslation\n', verse_content, flags=re.IGNORECASE)
            if len(v_parts) < 2: continue
            
            verse_text_part = v_parts[0].strip()
            after_trans_part = v_parts[1].strip()
            p_parts = re.split(r'\nPurport\n', after_trans_part, flags=re.IGNORECASE)
            translation_part = p_parts[0].strip()
            purport_raw = p_parts[1].strip() if len(p_parts) > 1 else None
            
            first_line_translit = ScriptureChunker.get_first_transliterated_line(verse_text_part)
            
            # Verse-Translation together
            combined_vt = f"Verse {verse_num}\n\n{verse_text_part}\n\nTranslation\n\n{translation_part}"
            chunks.append({
                "type": "verse+translation",
                "text": combined_vt,
                "verse_num": verse_num,
                "first_line_sloka": first_line_translit
            })
            
            if purport_raw:
                p_chunks = ScriptureChunker.split_into_normal_chunks(purport_raw)
                for sub_i, p_text in enumerate(p_chunks):
                    chunks.append({
                        "type": "commentary",
                        "text": f"Purport on Verse {verse_num} (Part {sub_i+1}):\n\n{p_text}",
                        "verse_num": verse_num,
                        "first_line_sloka": first_line_translit
                    })
        return chunks

    @staticmethod
    def generic_scripture_chunker(text, book_id):
        if "BrahmaSamhita" in book_id:
            return ScriptureChunker.chunk_brahma_samhita(text, book_id)
        elif "Bhagavad-gītā" in book_id or "Prapanna-jīvanāmṛtam" in book_id or "Prema-vivarta" in book_id:
            return ScriptureChunker.chunk_bhagavad_gita(text, book_id)
        else:
            return []
