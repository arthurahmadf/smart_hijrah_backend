# main/utils_rag/extractor.py
import re

def extract_claims(llm_response_text):
    if not llm_response_text:
        return "", []

    # Regex mencari blok [DALIL_START] ... [DALIL_END]
    pattern = r"\[DALIL_START\](.*?)\[DALIL_END\]"
    match = re.search(pattern, llm_response_text, re.DOTALL)

    claimed_sources = []
    clean_narration = llm_response_text

    if match:
        raw_claims_block = match.group(1).strip()
        # Hapus blok dalil dari narasi
        clean_narration = re.sub(pattern, "", llm_response_text, flags=re.DOTALL).strip()
        
        # Jika setelah dihapus malah kosong (berarti AI salah menaruh seluruh jawaban di dalam tag), kembalikan teks asal!
        if not clean_narration:
            clean_narration = llm_response_text.replace("[DALIL_START]", "").replace("[DALIL_END]", "").strip()

        if raw_claims_block:
            for line in raw_claims_block.split('\n'):
                line = line.strip().lstrip('- ').strip()
                if not line or '|' not in line:
                    continue
                
                parts = [p.strip() for p in line.split('|')]
                source_type = parts[0].upper() if len(parts) > 0 else ""

                try:
                    if source_type == "QURAN" and len(parts) >= 3:
                        claimed_sources.append({"type": "QURAN", "surah": int(parts[1]), "ayah": int(parts[2]), "raw": line})
                    elif source_type == "HADIS" and len(parts) >= 3:
                        kitab_name = parts[1].lower().replace(" ", "-")
                        claimed_sources.append({"type": "HADIS", "kitab": kitab_name, "nomor": int(parts[2]), "raw": line})
                    elif source_type == "EKSTERNAL" and len(parts) >= 2:
                        claimed_sources.append({"type": "EKSTERNAL", "detail": " ".join(parts[1:]), "raw": line})
                except ValueError:
                    continue
    else:
        # Debugging jika model lupa pakai tag [DALIL_START]
        print("[EXTRACTOR] Tag [DALIL_START] tidak ditemukan. Menggunakan seluruh teks sebagai narasi.")

    return clean_narration, claimed_sources