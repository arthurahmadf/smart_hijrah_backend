# main/utils_rag/final_checker.py
import re


HADITH_BOOK_ALIASES = {
    "bukhari": ["bukhari"],
    "muslim": ["muslim"],
    "abu-daud": ["abu daud", "abu-daud", "abu dawud", "dawud"],
    "tirmidzi": ["tirmidzi", "at tirmidzi", "at-tirmidzi"],
    "nasai": ["nasai", "nasa'i", "an nasai", "an-nasai"],
    "ibnu-majah": ["ibnu majah", "ibn majah", "ibnu-majah"],
    "malik": ["malik", "muwatta"],
    "ahmad": ["ahmad", "musnad ahmad"],
    "darimi": ["darimi", "ad darimi", "ad-darimi"],
}


SURAH_NAME_TO_NUMBER = {
    "al baqarah": 2,
    "al-baqarah": 2,
    "baqarah": 2,
    "ali imran": 3,
    "an nisa": 4,
    "al maidah": 5,
    "al an'am": 6,
    "al anam": 6,
    "al araf": 7,
    "al anfal": 8,
    "at taubah": 9,
    "yunus": 10,
    "hud": 11,
    "yusuf": 12,
    "ibrahim": 14,
    "al hijr": 15,
    "an nahl": 16,
    "al isra": 17,
    "al kahfi": 18,
    "maryam": 19,
    "taha": 20,
    "al anbiya": 21,
    "al hajj": 22,
    "al muminun": 23,
    "an nur": 24,
    "al furqan": 25,
    "asy syuara": 26,
    "an naml": 27,
    "al qasas": 28,
    "al ankabut": 29,
    "ar rum": 30,
    "luqman": 31,
    "yasin": 36,
    "az zumar": 39,
    "ghafir": 40,
    "muhammad": 47,
    "al fath": 48,
    "al hujurat": 49,
    "qaf": 50,
    "ar rahman": 55,
    "al waqiah": 56,
    "al mulk": 67,
    "al ikhlas": 112,
    "al falaq": 113,
    "an nas": 114,
}


def _norm(text):
    text = (text or "").lower()
    text = text.replace("’", "'")
    text = re.sub(r"[\u2010-\u2015]", "-", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _normalize_book_name(text):
    text = _norm(text)

    for slug, aliases in HADITH_BOOK_ALIASES.items():
        for alias in aliases:
            if alias in text:
                return slug

    return None


def _extract_verified_quran_set(verified_sources):
    result = set()

    for source in verified_sources or []:
        if source.get("type") != "QURAN" or not source.get("is_verified"):
            continue

        surah = source.get("surah_number")
        ayah = source.get("ayah_number")

        if surah and ayah:
            result.add((int(surah), int(ayah)))
            continue

        ref = _norm(source.get("reference", ""))

        match = re.search(r"\((\d{1,3})\)\s*:\s*(\d{1,3})", ref)
        if match:
            result.add((int(match.group(1)), int(match.group(2))))
            continue

        match = re.search(r"surah\s+(\d{1,3})\s*:\s*(\d{1,3})", ref)
        if match:
            result.add((int(match.group(1)), int(match.group(2))))
            continue

        # contoh: QS. Al Baqarah : 275
        match = re.search(r"qs\.?\s+(.+?)\s*:\s*(\d{1,3})", ref)
        if match:
            surah_name = match.group(1).strip()
            ayah_num = int(match.group(2))
            surah_num = SURAH_NAME_TO_NUMBER.get(surah_name)
            if surah_num:
                result.add((surah_num, ayah_num))

    return result


def _extract_verified_hadith_set(verified_sources):
    result = set()

    for source in verified_sources or []:
        if source.get("type") != "HADIS" or not source.get("is_verified"):
            continue

        book_slug = source.get("book_slug")
        number = source.get("number")

        if book_slug and number:
            result.add((_normalize_book_name(book_slug) or book_slug, int(number)))
            continue

        ref = _norm(source.get("reference", ""))
        book = _normalize_book_name(ref)

        match = re.search(r"(?:no|nomor|hadis|hadith)?\.?\s*(\d{1,7})\b", ref)
        if book and match:
            result.add((book, int(match.group(1))))

    return result


def _extract_claimed_quran_refs(text):
    text = _norm(text)
    claims = set()

    # QS 2:255 / Quran 2:255
    for match in re.finditer(r"\b(?:qs|q\.s\.|quran|al-qur'an|al quran)?\s*(\d{1,3})\s*:\s*(\d{1,3})", text):
        surah = int(match.group(1))
        ayah = int(match.group(2))
        if 1 <= surah <= 114:
            claims.add((surah, ayah))

    # QS. Al-Baqarah: 275 / Surah Al Baqarah ayat 275
    patterns = [
        r"\b(?:qs|q\.s\.|surah|surat)\.?\s+([a-zA-Z' -]+?)\s*[:\-]\s*(\d{1,3})",
        r"\b(?:qs|q\.s\.|surah|surat)\.?\s+([a-zA-Z' -]+?)\s+ayat\s+(\d{1,3})",
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, text):
            surah_name = match.group(1).strip()
            ayah = int(match.group(2))
            surah = SURAH_NAME_TO_NUMBER.get(surah_name)
            if surah:
                claims.add((surah, ayah))

    return claims


def _extract_claimed_hadith_refs(text):
    text = _norm(text)
    claims = set()

    for slug, aliases in HADITH_BOOK_ALIASES.items():
        for alias in aliases:
            # HR. Bukhari 3134 / Hadis Bukhari no. 1 / Sunan Abu Daud No. 5
            pattern = (
                r"\b(?:hr|hadis|hadits|sunan|shahih|sahih|musnad)?\.?\s*"
                + re.escape(alias)
                + r"\s*(?:no|nomor|hadis|hadith)?\.?\s*(\d{1,7})\b"
            )

            for match in re.finditer(pattern, text):
                claims.add((slug, int(match.group(1))))

    return claims


def apply_final_checks(reply, verified_sources, status_global):
    """
    Final checker sederhana.
    Tidak mengubah isi jawaban.
    Hanya:
    - mendeteksi rujukan QS/HR di narasi
    - membandingkan dengan verified_sources
    - menurunkan status jika ada mismatch
    """
    warnings = []
    reply = reply or ""

    verified_quran = _extract_verified_quran_set(verified_sources)
    verified_hadith = _extract_verified_hadith_set(verified_sources)

    claimed_quran = _extract_claimed_quran_refs(reply)
    claimed_hadith = _extract_claimed_hadith_refs(reply)

    for claim in sorted(claimed_quran):
        if claim not in verified_quran:
            warnings.append({
                "code": "UNVERIFIED_QURAN_REFERENCE_IN_NARRATION",
                "message": f"Narasi menyebut QS {claim[0]}:{claim[1]}, tetapi tidak ada di verified_sources.",
                "claim": {
                    "type": "QURAN",
                    "surah": claim[0],
                    "ayah": claim[1],
                }
            })

    for book, number in sorted(claimed_hadith):
        if (book, number) not in verified_hadith:
            warnings.append({
                "code": "UNVERIFIED_HADITH_REFERENCE_IN_NARRATION",
                "message": f"Narasi menyebut hadis {book} no. {number}, tetapi tidak ada di verified_sources.",
                "claim": {
                    "type": "HADIS",
                    "book": book,
                    "number": number,
                }
            })

    # Jika narasi memakai redaksi Rasulullah bersabda tapi tidak ada hadis verified.
    risky_prophetic_phrases = [
        "rasulullah bersabda",
        "nabi bersabda",
        "rasul saw bersabda",
        "rasulullah saw bersabda",
        "shallallahu 'alaihi wasallam bersabda",
        "shallallahu alaihi wasallam bersabda",
    ]

    if any(phrase in _norm(reply) for phrase in risky_prophetic_phrases) and not verified_hadith:
        warnings.append({
            "code": "PROPHETIC_QUOTE_WITHOUT_VERIFIED_HADITH",
            "message": "Narasi mengutip sabda Nabi, tetapi tidak ada hadis verified.",
        })

    # Jika narasi menyebut sahih/hasan/daif tapi verified source belum punya grading.
    grading_words = ["sahih", "shahih", "hasan", "daif", "dhaif", "maudhu"]
    if any(word in _norm(reply) for word in grading_words):
        has_hadith = any(s.get("type") == "HADIS" for s in verified_sources or [])
        if has_hadith:
            warnings.append({
                "code": "HADITH_GRADING_CLAIM_NEEDS_REVIEW",
                "message": "Narasi menyebut derajat hadis. Pastikan data grading/takhrij tersedia.",
            })

    final_status = status_global

    if warnings and status_global == "HIGH_CONFIDENCE":
        final_status = "NEEDS_REVIEW"

    return {
        "reply": reply,
        "verification_status": final_status,
        "final_check_warnings": warnings,
        "final_check_passed": len(warnings) == 0,
    }