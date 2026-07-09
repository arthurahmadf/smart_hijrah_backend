# main/utils_rag/verifier_guardrails.py
import re
from main.models_hadis import Hadis, KitabHadis
from main.models_tilawah import TilawahAyahPool
from main.utils_hadis.semantic_search import semantic_search_hadis

def _is_text_relevant(query, text):
    """Cek sederhana apakah teks hadis punya irisan kata dengan pertanyaan user"""
    if not text or not query:
        return False
    ignore_words = {"apa", "apakah", "bagaimana", "hukum", "dalam", "islam", "dan", "atau", "yang", "itu", "ini", "di", "ke", "dari", "dalil", "benarkah", "ada", "tentang", "tampilkan", "sebutkan", "hadis", "surah", "ayat", "no", "nomor", "riwayat", "hr"}
    query_words = set(query.lower().split()) - ignore_words
    
    # Jika query setelah dibersihkan ternyata KOSONG (berarti user cuma minta nomor/identitas dalil), anggap RELEVAN!
    if not query_words:
        return True

    text_lower = text.lower()
    for w in query_words:
        if len(w) > 3 and w in text_lower:
            return True
    return False

def verify_and_apply_guardrails(claims, user_query=""):
    verified_sources = []
    all_high_confidence = True

    # Deteksi apakah user secara eksplisit meminta nomor tertentu (misal: "no 3", "nomor 109282", "ayat 183")
    has_explicit_number = bool(re.search(r'\b(no|nomor|n|#)?\s*\d+\b', user_query.lower()))

    for claim in claims:
        stype = claim.get("type")
        
        # ---------------------------------------------------------
        # 1. VERIFIKASI AL-QUR'AN (Dengan Anti-0|0 Bug)
        # ---------------------------------------------------------
        if stype == "QURAN":
            try:
                surah_num = int(claim.get("surah", 0))
                ayah_num = int(claim.get("ayah", 0))
            except (ValueError, TypeError):
                continue
            
            # SANITIZER: Abaikan halusinasi angka 0 atau negatif dari LLM!
            if surah_num <= 0 or ayah_num <= 0:
                print(f"[GUARDRAIL SANITIZER] Membuang halusinasi metadata Quran tidak valid: {surah_num}|{ayah_num}")
                continue

            ayah_obj = TilawahAyahPool.objects.filter(
                surah_number=surah_num,
                ayah_number=ayah_num
            ).first()
            if ayah_obj:
                verified_sources.append({
                    "type": "QURAN",
                    "label": "Terverifikasi ✅ (Kalamullah - Wahyu Mutlak)",
                    "reference": f"QS. {ayah_obj.surah_name} : {ayah_obj.ayah_number}",
                    "arabic_text": getattr(ayah_obj, 'ayah_text', ''),
                    "translation_text": getattr(ayah_obj, 'ayah_translation', ''),
                    "is_verified": True
                })
            else:
                all_high_confidence = False
                verified_sources.append({
                    "type": "QURAN", "label": "Belum Terverifikasi ⚠️ (Ayat tidak ditemukan di DB)",
                    "reference": f"QS. Surah {surah_num} : {ayah_num}", "is_verified": False
                })

        # ---------------------------------------------------------
        # 2. VERIFIKASI HADIS (Dengan Anti-Nomor Hantu / Out of Bounds)
        # ---------------------------------------------------------
        elif stype == "HADIS":
            kitab_slug = str(claim.get("kitab", "")).lower()
            try:
                nomor = int(claim.get("nomor", 0))
            except (ValueError, TypeError):
                continue
            
            # SANITIZER: Abaikan nomor hadis 0 atau negatif
            if nomor <= 0:
                continue

            # Cari exact match berdasarkan angka
            hadis_obj = Hadis.objects.filter(kitab__nama_file__icontains=kitab_slug, nomor=nomor).first()
            
            is_relevant = True
            if hadis_obj:
                # JIKA user meminta nomor eksplisit DAN ketemu di DB -> LANGSUNG PERCAYA! (Bypass Relevansi)
                if has_explicit_number:
                    is_relevant = True
                    print(f"[GUARDRAIL OVERRIDE] User meminta nomor eksplisit. HR {kitab_slug} No. {nomor} dikunci dari DB!")
                else:
                    terjemahan = hadis_obj.terjemahan or hadis_obj.isi_hadis
                    is_relevant = _is_text_relevant(user_query, terjemahan)
            
            # IMPROVISASI KRITIS: Jika user minta nomor eksplisit (misal No. 109282) dan TIDAK KETEMU,
            # JANGAN lakukan Semantic Search! Langsung vonis Tidak Ditemukan!
            if not hadis_obj or not is_relevant:
                if has_explicit_number and not hadis_obj:
                    print(f"[GUARDRAIL BLOCK] Nomor eksplisit HR {kitab_slug} No. {nomor} TIDAK ADA DI DB! Memblokir Semantic Fallback.")
                    hadis_obj = None # Biarkan None agar jatuh ke status Belum Terverifikasi
                else:
                    # Hanya lakukan semantic search jika user TIDAK sedang mencari nomor eksplisit
                    search_query = f"{user_query} {kitab_slug}"
                    fallback_results = semantic_search_hadis(search_query, limit=1, threshold=0.55)
                    if fallback_results:
                        hadis_obj = fallback_results[0]
                        print(f"[GUARDRAIL SUCCESS] Fallback berhasil! Menemukan HR {hadis_obj.kitab.nama_indonesia} No. {hadis_obj.nomor}.")
                    else:
                        hadis_obj = None 
            
            if hadis_obj:
                label = "Ditemukan di Database ✅ (Derajat hadis belum ditampilkan)"

                verified_sources.append({
                    "type": "HADIS", "label": label,
                    "reference": f"{hadis_obj.kitab.nama_indonesia} No. {hadis_obj.nomor}",
                    "arabic_text": hadis_obj.teks_arab or hadis_obj.teks_hadis,
                    "translation_text": hadis_obj.terjemahan or hadis_obj.isi_hadis,
                    "is_verified": True
                })
            else:
                all_high_confidence = False
                verified_sources.append({
                    "type": "HADIS", "label": "Belum Terverifikasi ⚠️ (Nomor hadis tidak ditemukan di DB)",
                    "reference": f"HR. {kitab_slug.title()} No. {nomor} (Tidak Terdapat dalam Kitab)", "is_verified": False
                })

        # ---------------------------------------------------------
        # 3. RUJUKAN EKSTERNAL
        # ---------------------------------------------------------
        elif stype == "EKSTERNAL":
            detail_text = str(claim.get("detail", ""))
            if "116" in detail_text and "paylater" not in user_query.lower() and "uang" not in user_query.lower():
                continue 
                
            verified_sources.append({
                "type": "EKSTERNAL", "label": "Rujukan Eksternal ℹ️ (Kajian Ulama/Fatwa)",
                "reference": detail_text, "is_verified": True
            })

    status_global = "HIGH_CONFIDENCE" if all_high_confidence and len(verified_sources) > 0 else "NEEDS_REVIEW"
    return verified_sources, status_global