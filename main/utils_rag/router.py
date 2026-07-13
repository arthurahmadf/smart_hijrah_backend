# main/utils_rag/router.py
import re
from main.utils_rag.reference_parser import (
    parse_direct_hadith_reference,
    parse_direct_quran_reference,
)


class IntentType:
    DIRECT_HADITH_LOOKUP = "DIRECT_HADITH_LOOKUP"
    DIRECT_QURAN_LOOKUP = "DIRECT_QURAN_LOOKUP"
    THEMATIC_DALIL_SEARCH = "THEMATIC_DALIL_SEARCH"
    FIQH_QA = "FIQH_QA"
    FATWA_QA = "FATWA_QA"
    SPIRITUAL_ADVICE = "SPIRITUAL_ADVICE"
    GENERAL_ISLAMIC_QA = "GENERAL_ISLAMIC_QA"
    OUT_OF_DOMAIN = "OUT_OF_DOMAIN"


def normalize(text: str) -> str:
    text = (text or "").lower().strip()
    text = text.replace("ḥ", "h").replace("ṣ", "s").replace("ḍ", "d")
    text = text.replace("ṭ", "t").replace("ż", "z").replace("’", "'")
    text = re.sub(r"\s+", " ", text)
    return text


def contains_any(text: str, keywords):
    for keyword in keywords:
        keyword = keyword.strip().lower()

        if not keyword:
            continue

        # Keyword sangat pendek harus cocok sebagai kata utuh.
        if len(keyword) <= 3:
            pattern = r"(?<!\w)" + re.escape(keyword) + r"(?!\w)"
            if re.search(pattern, text):
                return True
        elif keyword in text:
            return True

    return False


def matches_any(text: str, patterns):
    return any(re.search(pattern, text) for pattern in patterns)


def detect_normative_islamic_intent(text: str) -> bool:
    """
    Deteksi apakah user sedang bertanya hukum/nilai Islam.
    Ini lebih penting daripada objek pertanyaannya.

    Contoh yang harus True:
    - apa hukum trading saham
    - nonton anime hentai apa boleh
    - bolehkah kerja di bank
    - halal atau haram investasi crypto
    - berdosa tidak kalau ...
    """
    normative_patterns = [
        r"\bapa hukum\b",
        r"\bhukumnya\b",
        r"\bbagaimana hukum\b",
        r"\bbolehkah\b",
        r"\bapa boleh\b",
        r"\bboleh tidak\b",
        r"\bboleh gak\b",
        r"\bboleh nggak\b",
        r"\bboleh kah\b",
        r"\bhalal\b",
        r"\bharam\b",
        r"\bdosa\b",
        r"\bberdosa\b",
        r"\bpahala\b",
        r"\bberpahala\b",
        r"\bsah tidak\b",
        r"\bsahkah\b",
        r"\bbatal tidak\b",
        r"\bmembatalkan\b",
        r"\bmenurut islam\b",
        r"\bdalam islam\b",
        r"\bpandangan islam\b",
        r"\bsecara islam\b",
        r"\bsecara syariat\b",
        r"\bmenurut syariat\b",
        r"\bmenurut fiqih\b",
        r"\bmenurut fikih\b",
        r"\bsyariah\b",
        r"\bsyar'i\b",
        r"\bsyari\b",
    ]

    return matches_any(text, normative_patterns)


def detect_thematic_dalil_intent(text: str) -> bool:
    patterns = [
        r"\bdalil\b",
        r"\bayat tentang\b",
        r"\bhadis tentang\b",
        r"\bhadits tentang\b",
        r"\bquran tentang\b",
        r"\bal quran tentang\b",
        r"\bapa dalil\b",
        r"\bsebutkan dalil\b",
        r"\bcarikan dalil\b",
        r"\briwayat tentang\b",
    ]
    return matches_any(text, patterns)


def detect_spiritual_advice_intent(text: str) -> bool:
    advice_keywords = [
        # kondisi hati
        "aku merasa",
        "saya merasa",
        "gelisah",
        "sedih",
        "cemas",
        "takut",
        "putus asa",
        "hati kosong",
        "hati gelisah",
        "hati tidak tenang",

        # hubungan dengan Allah
        "jauh dari allah",
        "merasa jauh dari allah",
        "ingin dekat dengan allah",

        # iman
        "iman turun",
        "imanku turun",
        "imanku lagi turun",
        "iman sedang turun",
        "iman lemah",
        "imanku lemah",
        "futur",

        # taubat
        "ingin taubat",
        "ingin bertaubat",
        "mau taubat",
        "mau bertaubat",
        "cara taubat",
        "cara bertaubat",
        "sering jatuh lagi",
        "mengulangi dosa",
        "kembali melakukan dosa",
        "merasa berdosa",

        # shalat dan istiqamah
        "malas shalat",
        "malas sholat",
        "susah istiqamah",
        "sulit istiqamah",
        "sering meninggalkan shalat",
        "sering meninggalkan sholat",
        "ingin berubah",
        "ingin memperbaiki diri",

        # hijrah
        "ingin hijrah",
        "cara hijrah",
        "tips istiqamah",
    ]

    if contains_any(text, advice_keywords):
        return True

    advice_patterns = [
        r"\b(?:aku|saya)\s+ingin\s+(?:berubah|bertaubat|taubat|hijrah)\b",
        r"\b(?:aku|saya)\s+sering\s+(?:jatuh|mengulangi dosa|meninggalkan shalat|meninggalkan sholat)\b",
        r"\biman(?:ku)?\s+(?:lagi\s+|sedang\s+)?turun\b",
        r"\bharus bagaimana\b",
        r"\bbagaimana agar istiqamah\b",
    ]

    return matches_any(text, advice_patterns)


def detect_fatwa_category(text: str) -> bool:
    """
    Ini bukan daftar semua objek fiqih.
    Ini hanya kategori yang biasanya butuh fatwa/kajian kontemporer.
    Kalau tidak kena kategori ini tapi normative intent True, fallback ke FIQH_QA.
    """
    fatwa_category_keywords = [
        # lembaga / fatwa
        "fatwa",
        "mui",
        "dsn",
        "dsn-mui",
        "nu",
        "nahdlatul ulama",
        "muhammadiyah",
        "tarjih",
        "bahtsul masail",
        "kemenag",

        # muamalah kontemporer
        "paylater",
        "pay later",
        "pinjol",
        "pinjaman online",
        "bank",
        "bank syariah",
        "asuransi",
        "bpjs",
        "leasing",
        "kredit",
        "cicilan",
        "kartu kredit",
        "e-wallet",
        "ewallet",
        "dompet digital",
        "fintech",

        # investasi / finansial
        "saham",
        "trading",
        "forex",
        "crypto",
        "kripto",
        "bitcoin",
        "investasi",
        "reksadana",
        "reksa dana",
        "obligasi",
        "sukuk",
        "emas digital",

        # kontemporer medis/sosial
        "vaksin",
        "transplantasi",
        "bayi tabung",
        "donor organ",
        "operasi plastik",
        "tes dna",
        "kloning",

        # teknologi modern
        "artificial intelligence",
        "kecerdasan buatan",
        "marketplace",
        "artificial intelligence",
        "kecerdasan buatan",
        "teknologi ai",
        "penggunaan ai",
    ]

    return contains_any(text, fatwa_category_keywords)


def detect_clear_non_islamic_task(text: str) -> bool:
    """
    Deteksi permintaan bantuan non-Islam yang jelas.
    Ini bukan untuk pertanyaan hukum Islam.
    """
    non_islamic_task_patterns = [
        # coding task
        r"\bbuatkan kode\b",
        r"\bbikin kode\b",
        r"\btulis kode\b",
        r"\bdebug\b",
        r"\bfix bug\b",
        r"\bsorting array\b",
        r"\bcontoh program\b",
        r"\bscript python\b",
        r"\bkode python\b",

        # generic creation/search unrelated
        r"\bbuatkan resep\b",
        r"\bresep\b",
        r"\brekomendasi anime\b",
        r"\brekomendasi film\b",
        r"\brekomendasi game\b",
        r"\bcarikan hotel\b",
        r"\bcarikan tiket\b",
        r"\bberapa harga\b",
        r"\bcuaca\b",
    ]

    return matches_any(text, non_islamic_task_patterns)


def detect_non_islamic_subject_signal(text: str) -> bool:
    """
    Sinyal topik non-Islam. Ini tidak otomatis diblokir.
    Kalau user bertanya hukum Islam tentang topik ini, tetap boleh masuk FIQH_QA/FATWA_QA.
    """
    subject_keywords = [
        "coding",
        "kode",
        "program",
        "programming",
        "python",
        "javascript",
        "java",
        "php",
        "laravel",
        "django",
        "flutter",
        "react",
        "nodejs",
        "sql",
        "database",
        "api",
        "html",
        "css",

        "resep",
        "masakan",
        "game",
        "anime",
        "film",
        "movie",
        "hentai",
        "pornografi",
        "porno",

        "saham",
        "trading",
        "forex",
        "bitcoin",
        "crypto price",
        "harga bitcoin",
        "cuaca",
        "hotel",
        "tiket pesawat",
    ]

    return contains_any(text, subject_keywords)


def detect_islamic_signal(text: str) -> bool:
    islam_keywords = [
        "islam",
        "muslim",
        "muslimah",
        "allah",
        "rasul",
        "rasulullah",
        "nabi",
        "sahabat",
        "ulama",
        "ustadz",
        "ustaz",
        "kyai",
        "quran",
        "al quran",
        "alquran",
        "qs",
        "surah",
        "surat",
        "ayat",
        "hadis",
        "hadits",
        "hr",
        "riwayat",
        "shalat",
        "sholat",
        "wudhu",
        "puasa",
        "zakat",
        "sedekah",
        "haji",
        "umrah",
        "fiqih",
        "fikih",
        "akhlak",
        "dosa",
        "pahala",
        "halal",
        "haram",
        "sunnah",
        "wajib",
        "makruh",
        "mubah",
        "doa",
        "dzikir",
        "zikir",
        "taubat",
        "hijrah",
        "istiqamah",
        "imam",
        "makmum",
        "masjid",
        "musholla",
        "mushala",
        "mazhab",
        "fatwa",
        "mui",
        "nu",
        "muhammadiyah",
        "waris",
        "faraid",
        "nikah",
        "talak",
        "cerai",
        "haid",
        "najis",
        "syariat",
        "syariah",
        "syar'i",
    ]

    return contains_any(text, islam_keywords)


def classify_intent(user_message: str):
    text = normalize(user_message)

    # =========================================================
    # 1. DIRECT LOOKUP HARUS PALING AWAL
    # Karena deterministic dan tidak perlu LLM.
    # =========================================================

    quran_ref = parse_direct_quran_reference(text)
    if quran_ref:
        return {
            "intent": IntentType.DIRECT_QURAN_LOOKUP,
            "confidence": 0.98,
            "entities": quran_ref,
            "route": "direct_lookup",
        }

    hadith_ref = parse_direct_hadith_reference(text)
    if hadith_ref:
        return {
            "intent": IntentType.DIRECT_HADITH_LOOKUP,
            "confidence": hadith_ref.get("confidence", 0.95),
            "entities": hadith_ref,
            "route": "direct_lookup",
        }

    # =========================================================
    # 2. HITUNG SINYAL INTENT
    # =========================================================

    has_strong_normative = detect_strong_normative_intent(text)
    has_weak_permission = detect_weak_permission_intent(text)

    has_clear_non_islamic_task = detect_clear_non_islamic_task(text)
    has_islamic_signal = detect_islamic_signal(text)

    has_normative = (
        has_strong_normative
        or (
            has_weak_permission
            and (
                has_islamic_signal
                or not has_clear_non_islamic_task
            )
        )
    )
    has_fatwa_category = detect_fatwa_category(text)
    has_spiritual_advice = detect_spiritual_advice_intent(text)
    has_thematic_dalil = detect_thematic_dalil_intent(text)
    has_clear_non_islamic_task = detect_clear_non_islamic_task(text)
    has_non_islamic_subject = detect_non_islamic_subject_signal(text)
    has_islamic_signal = detect_islamic_signal(text)

    # =========================================================
    # 3. CLEAR NON-ISLAMIC TASK
    # Blokir hanya jika user memang meminta tugas non-Islam,
    # dan bukan sedang bertanya hukum Islam.
    # =========================================================

    if has_clear_non_islamic_task and not has_strong_normative and not has_islamic_signal:
        return {
            "intent": IntentType.OUT_OF_DOMAIN,
            "confidence": 0.94,
            "entities": {},
            "route": "blocked",
            "blocked_reason": "Permintaan merupakan tugas non-Islam tanpa konteks Islam.",
        }

    if has_clear_non_islamic_task and not has_normative and not has_islamic_signal:
        return {
            "intent": IntentType.OUT_OF_DOMAIN,
            "confidence": 0.92,
            "entities": {},
            "route": "blocked",
            "blocked_reason": "Permintaan merupakan tugas non-Islam tanpa konteks hukum Islam.",
            "signals": {
                "has_clear_non_islamic_task": has_clear_non_islamic_task,
                "has_normative": has_normative,
                "has_islamic_signal": has_islamic_signal,
            }
        }

    # =========================================================
    # 4. NORMATIVE ISLAMIC QUESTION
    # Ini inti patch.
    # Objek apa pun boleh masuk selama user bertanya hukum Islam.
    # =========================================================

    if has_normative:
        if has_fatwa_category:
            return {
                "intent": IntentType.FATWA_QA,
                "confidence": 0.88,
                "entities": {},
                "route": "metode7",
                "reason": "Pertanyaan hukum Islam dengan kategori kontemporer/fatwa.",
                "signals": {
                    "has_normative": has_normative,
                    "has_fatwa_category": has_fatwa_category,
                }
            }

        return {
            "intent": IntentType.FIQH_QA,
            "confidence": 0.86,
            "entities": {},
            "route": "metode7",
            "reason": "Pertanyaan hukum Islam umum.",
            "signals": {
                "has_normative": has_normative,
                "has_fatwa_category": has_fatwa_category,
            }
        }

    # =========================================================
    # 5. SPIRITUAL ADVICE
    # Setelah normative. Karena "aku merasa berdosa..." bisa hukum,
    # tapi "aku merasa jauh dari Allah" lebih cocok nasihat.
    # =========================================================

    if has_spiritual_advice:
        return {
            "intent": IntentType.SPIRITUAL_ADVICE,
            "confidence": 0.82,
            "entities": {},
            "route": "metode7",
            "reason": "User membutuhkan nasihat spiritual.",
        }

    # =========================================================
    # 6. THEMATIC DALIL SEARCH
    # =========================================================

    if has_thematic_dalil:
        return {
            "intent": IntentType.THEMATIC_DALIL_SEARCH,
            "confidence": 0.85,
            "entities": {},
            "route": "metode7",
            "reason": "User mencari dalil tematik.",
        }

    # =========================================================
    # 7. FATWA CATEGORY TANPA POLA HUKUM
    # Contoh: "fatwa MUI paylater", "MUI crypto"
    # =========================================================

    if has_fatwa_category and has_islamic_signal:
        return {
            "intent": IntentType.FATWA_QA,
            "confidence": 0.8,
            "entities": {},
            "route": "metode7",
            "reason": "Ada sinyal fatwa/kontemporer dan sinyal Islam.",
        }

    # =========================================================
    # 8. NON-ISLAMIC SUBJECT TANPA KONTEXT ISLAM
    # Contoh:
    # - "jelaskan recursion"
    # - "aku merasa kamu bisa bikin kode python"
    # =========================================================

    if has_non_islamic_subject and not has_islamic_signal:
        return {
            "intent": IntentType.OUT_OF_DOMAIN,
            "confidence": 0.82,
            "entities": {},
            "route": "blocked",
            "blocked_reason": "Topik non-Islam tanpa konteks Islam.",
            "signals": {
                "has_non_islamic_subject": has_non_islamic_subject,
                "has_islamic_signal": has_islamic_signal,
            }
        }

    # =========================================================
    # 9. GENERIC REQUEST TANPA SINYAL ISLAM
    # =========================================================

    generic_request_patterns = [
        r"\bbuatkan\b",
        r"\bbikin\b",
        r"\btolong buat\b",
        r"\bcarikan\b",
        r"\bjelaskan\b",
        r"\bapa itu\b",
    ]

    if not has_islamic_signal and matches_any(text, generic_request_patterns):
        return {
            "intent": IntentType.OUT_OF_DOMAIN,
            "confidence": 0.75,
            "entities": {},
            "route": "blocked",
            "blocked_reason": "Tidak ditemukan konteks Islam pada permintaan umum.",
        }

    # =========================================================
    # 10. DEFAULT
    # Untuk saat ini tetap masuk Metode 7.
    # Nanti bisa ditambah LLM classifier fallback.
    # =========================================================

    return {
        "intent": IntentType.GENERAL_ISLAMIC_QA,
        "confidence": 0.6,
        "entities": {},
        "route": "metode7",
        "reason": "Default general Islamic QA.",
    }

def detect_strong_normative_intent(text: str) -> bool:
    patterns = [
        r"\bapa hukum\b",
        r"\bbagaimana hukum\b",
        r"\bhukumnya\b",
        r"\bhalal\b",
        r"\bharam\b",
        r"\bdosa\b",
        r"\bberdosa\b",
        r"\bpahala\b",
        r"\bsahkah\b",
        r"\bsah tidak\b",
        r"\bmenurut islam\b",
        r"\bdalam islam\b",
        r"\bpandangan islam\b",
        r"\bmenurut syariat\b",
        r"\bsecara syariat\b",
        r"\bmenurut fiqih\b",
        r"\bmenurut fikih\b",
    ]
    return matches_any(text, patterns)


def detect_weak_permission_intent(text: str) -> bool:
    patterns = [
        r"\bbolehkah\b",
        r"\bapa boleh\b",
        r"\bboleh tidak\b",
        r"\bboleh gak\b",
        r"\bboleh nggak\b",
    ]
    return matches_any(text, patterns)