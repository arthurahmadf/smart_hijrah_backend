# main/utils_rag/reference_parser.py
import re


HADITH_BOOK_ALIASES = {
    "bukhari": [
        "bukhari",
        "bukhori",
        "bukari",
        "bokhari",
        "al bukhari",
        "al-bukhari",
        "al bukhori",
        "shahih bukhari",
        "sahih bukhari",
        "shahih bukhori",
        "sahih bukhori",
        "hr bukhari",
        "hr bukhori",
    ],
    "muslim": [
        "muslim", "shahih muslim", "sahih muslim", "hr muslim"
    ],
    "abu-daud": [
        "abu daud",
        "abu-daud",
        "abudaud",
        "abu dawud",
        "abu-dawud",
        "abudawud",
        "dawud",
        "daud",
        "sunan abu daud",
        "sunan abu dawud",
        "hr abu daud",
        "hr abu dawud",
    ],
    "tirmidzi": [
        "tirmidzi", "at tirmidzi", "at-tirmidzi", "turmudzi",
        "sunan tirmidzi", "hr tirmidzi"
    ],
    "nasai": [
        "nasai", "nasa'i", "an nasai", "an-nasai", "an nasa'i",
        "sunan nasai", "hr nasai"
    ],
    "ibnu-majah": [
        "ibnu majah", "ibn majah", "ibnu-majah", "ibn-majah",
        "sunan ibnu majah", "sunan ibn majah", "hr ibnu majah"
    ],
    "malik": [
        "malik", "imam malik", "muwatta malik", "al muwatta", "muwatha malik",
        "hr malik"
    ],
    "ahmad": [
        "ahmad", "imam ahmad", "musnad ahmad", "hr ahmad"
    ],
    "darimi": [
        "darimi", "ad darimi", "ad-darimi", "sunan darimi", "hr darimi"
    ],
}


DIRECT_LOOKUP_KEYWORDS = [
    "tampilkan",
    "lihat",
    "carikan",
    "cari",
    "hadis",
    "hadits",
    "hr",
    "riwayat",
    "nomor",
    "no",
    "no.",
]


def normalize_text(text: str) -> str:
    text = (text or "").lower().strip()
    text = text.replace("ḥ", "h").replace("ṣ", "s").replace("ḍ", "d")
    text = text.replace("ṭ", "t").replace("ż", "z").replace("’", "'")
    text = re.sub(r"\s+", " ", text)
    return text


def extract_hadith_number(text: str):
    """
    Ambil nomor hadis dari pola:
    - no 5
    - no. 5
    - nomor 5
    - hadis abu daud 5
    - hr abu daud no 5
    """
    text = normalize_text(text)

    patterns = [
        r"\b(?:no|no\.|nomor|number|#)\s*[:\-]?\s*(\d{1,7})\b",
        r"\b(?:hadis|hadits|hr|riwayat)\b.*?\b(\d{1,7})\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None

    return None


def detect_hadith_book(text: str):
    """
    Return:
    {
        "slug": "abu-daud",
        "matched_alias": "abu daud",
        "confidence": 0.95,
        "is_ambiguous": False
    }
    """
    text = normalize_text(text)

    matches = []

    for slug, aliases in HADITH_BOOK_ALIASES.items():
        for alias in aliases:
            alias_norm = normalize_text(alias)
            pattern = r"(?<!\w)" + re.escape(alias_norm) + r"(?!\w)"
            if re.search(pattern, text):
                matches.append((slug, alias_norm))

    if not matches:
        return None

    # Pilih alias terpanjang agar "abu daud" menang atas "daud"
    matches.sort(key=lambda x: len(x[1]), reverse=True)
    slug, alias = matches[0]

    # Khusus "daud/dawud" saja, anggap ambiguous tapi boleh normalisasi ke Abu Daud
    is_ambiguous = alias in {"daud", "dawud"}

    return {
        "slug": slug,
        "matched_alias": alias,
        "confidence": 0.75 if is_ambiguous else 0.95,
        "is_ambiguous": is_ambiguous,
    }


def parse_direct_hadith_reference(user_message: str):
    """
    Deteksi apakah user meminta hadis spesifik berdasarkan kitab + nomor.

    Return None jika bukan direct lookup.
    Return dict jika direct lookup:
    {
        "type": "hadith",
        "book_slug": "abu-daud",
        "number": 5,
        "confidence": 0.95,
        "is_ambiguous": False,
        "assumption_note": ""
    }
    """
    text = normalize_text(user_message)

    book = detect_hadith_book(text)
    number = extract_hadith_number(text)

    if not book or not number:
        return None

    assumption_note = ""
    if book["is_ambiguous"]:
        assumption_note = (
            f"Saya menafsirkan maksud Anda sebagai Sunan Abu Daud no. {number}, "
            "karena istilah 'Daud' dalam konteks hadis biasanya merujuk pada Abu Daud."
        )

    return {
        "type": "hadith",
        "book_slug": book["slug"],
        "number": number,
        "confidence": book["confidence"],
        "is_ambiguous": book["is_ambiguous"],
        "matched_alias": book["matched_alias"],
        "assumption_note": assumption_note,
    }

# =========================
# QURAN DIRECT LOOKUP
# =========================

SURAH_ALIASES = {
    1: ["al fatihah", "alfatihah", "fatihah"],
    2: ["al baqarah", "al-baqarah", "albaqarah", "baqarah"],
    3: ["ali imran", "ali-imran", "alimran"],
    4: ["an nisa", "an-nisa", "annisa", "nisa"],
    5: ["al maidah", "al-maidah", "almaidah", "maidah"],
    6: ["al anam", "al-anam", "alanam", "an am"],
    7: ["al araf", "al-araf", "alaraf", "araf"],
    8: ["al anfal", "al-anfal", "alanfal", "anfal"],
    9: ["at taubah", "at-taubah", "attaubah", "taubah"],
    10: ["yunus"],
    11: ["hud"],
    12: ["yusuf"],
    13: ["ar rad", "ar-rad", "arrad", "rad"],
    14: ["ibrahim"],
    15: ["al hijr", "al-hijr", "alhijr", "hijr"],
    16: ["an nahl", "an-nahl", "annahl", "nahl"],
    17: ["al isra", "al-isra", "alisra", "isra"],
    18: ["al kahfi", "al-kahfi", "alkahfi", "kahfi"],
    19: ["maryam"],
    20: ["taha", "tha ha", "thaha"],
    21: ["al anbiya", "al-anbiya", "alanbiya", "anbiya"],
    22: ["al hajj", "al-hajj", "alhajj", "hajj"],
    23: ["al muminun", "al-muminun", "almuminun", "muminun"],
    24: ["an nur", "an-nur", "annur", "nur"],
    25: ["al furqan", "al-furqan", "alfurqan", "furqan"],
    26: ["asy syuara", "asy-syuara", "assyuara", "syuara"],
    27: ["an naml", "an-naml", "annaml", "naml"],
    28: ["al qasas", "al-qasas", "alqasas", "qasas"],
    29: ["al ankabut", "al-ankabut", "alankabut", "ankabut"],
    30: ["ar rum", "ar-rum", "arrum", "rum"],
    31: ["luqman"],
    32: ["as sajdah", "as-sajdah", "assajdah", "sajdah"],
    33: ["al ahzab", "al-ahzab", "alahzab", "ahzab"],
    34: ["saba"],
    35: ["fatir", "fathir"],
    36: ["yasin", "ya sin", "yaa siin"],
    37: ["as saffat", "as-saffat", "assaffat", "saffat"],
    38: ["sad", "shaad"],
    39: ["az zumar", "az-zumar", "azzumar", "zumar"],
    40: ["ghafir", "al mumin", "al-mumin"],
    41: ["fussilat", "fushshilat"],
    42: ["asy syura", "asy-syura", "asshyura", "syura"],
    43: ["az zukhruf", "az-zukhruf", "azzukhruf", "zukhruf"],
    44: ["ad dukhan", "ad-dukhan", "addukhan", "dukhan"],
    45: ["al jasiyah", "al-jasiyah", "aljasiyah", "jasiyah"],
    46: ["al ahqaf", "al-ahqaf", "alahqaf", "ahqaf"],
    47: ["muhammad"],
    48: ["al fath", "al-fath", "alfath", "fath"],
    49: ["al hujurat", "al-hujurat", "alhujurat", "hujurat"],
    50: ["qaf"],
    51: ["az zariyat", "az-zariyat", "azzariyat", "zariyat", "dzariyat"],
    52: ["at tur", "at-tur", "attur", "tur"],
    53: ["an najm", "an-najm", "annajm", "najm"],
    54: ["al qamar", "al-qamar", "alqamar", "qamar"],
    55: ["ar rahman", "ar-rahman", "arrahman", "rahman"],
    56: ["al waqiah", "al-waqiah", "alwaqiah", "waqiah"],
    57: ["al hadid", "al-hadid", "alhadid", "hadid"],
    58: ["al mujādilah", "al mujadilah", "al-mujadilah", "mujadilah"],
    59: ["al hasyr", "al-hasyr", "alhasyr", "hasyr"],
    60: ["al mumtahanah", "al-mumtahanah", "mumtahanah"],
    61: ["as saff", "as-saff", "assaff", "saff"],
    62: ["al jumuah", "al-jumuah", "jumuah"],
    63: ["al munafiqun", "al-munafiqun", "munafiqun"],
    64: ["at taghabun", "at-taghabun", "taghabun"],
    65: ["at talaq", "at-talaq", "talaq"],
    66: ["at tahrim", "at-tahrim", "tahrim"],
    67: ["al mulk", "al-mulk", "mulk"],
    68: ["al qalam", "al-qalam", "qalam"],
    69: ["al haqqah", "al-haqqah", "haqqah"],
    70: ["al maarij", "al-maarij", "maarij"],
    71: ["nuh"],
    72: ["al jinn", "al-jinn", "jinn"],
    73: ["al muzzammil", "al-muzzammil", "muzzammil"],
    74: ["al muddassir", "al-muddassir", "muddassir"],
    75: ["al qiyamah", "al-qiyamah", "qiyamah"],
    76: ["al insan", "al-insan", "insan"],
    77: ["al mursalat", "al-mursalat", "mursalat"],
    78: ["an naba", "an-naba", "naba"],
    79: ["an naziat", "an-naziat", "naziat"],
    80: ["abasa"],
    81: ["at takwir", "at-takwir", "takwir"],
    82: ["al infitar", "al-infitar", "infitar"],
    83: ["al mutaffifin", "al-mutaffifin", "mutaffifin"],
    84: ["al insyiqaq", "al-insyiqaq", "insyiqaq"],
    85: ["al buruj", "al-buruj", "buruj"],
    86: ["at tariq", "at-tariq", "tariq"],
    87: ["al ala", "al-a'la", "ala"],
    88: ["al ghasyiyah", "al-ghasyiyah", "ghasyiyah"],
    89: ["al fajr", "al-fajr", "fajr"],
    90: ["al balad", "al-balad", "balad"],
    91: ["asy syams", "asy-syams", "syams"],
    92: ["al lail", "al-lail", "lail"],
    93: ["ad duha", "ad-duha", "duha", "dhuha"],
    94: ["al insyirah", "al-insyirah", "insyirah"],
    95: ["at tin", "at-tin", "tin"],
    96: ["al alaq", "al-alaq", "alaq"],
    97: ["al qadr", "al-qadr", "qadr"],
    98: ["al bayyinah", "al-bayyinah", "bayyinah"],
    99: ["az zalzalah", "az-zalzalah", "zalzalah"],
    100: ["al adiyat", "al-adiyat", "adiyat"],
    101: ["al qariah", "al-qariah", "qariah"],
    102: ["at takasur", "at-takasur", "takasur"],
    103: ["al asr", "al-asr", "asr"],
    104: ["al humazah", "al-humazah", "humazah"],
    105: ["al fil", "al-fil", "fil"],
    106: ["quraisy", "quraish"],
    107: ["al maun", "al-maun", "maun"],
    108: ["al kautsar", "al-kautsar", "kautsar"],
    109: ["al kafirun", "al-kafirun", "kafirun"],
    110: ["an nasr", "an-nasr", "nasr"],
    111: ["al lahab", "al-lahab", "lahab"],
    112: ["al ikhlas", "al-ikhlas", "ikhlas"],
    113: ["al falaq", "al-falaq", "falaq"],
    114: ["an nas", "an-nas", "annas", "nas"],
}


def detect_surah(text: str):
    text = normalize_text(text)

    numeric_patterns = [
        r"\b(?:qs|q\.s\.|quran|al quran|surah|surat)\s*[:\-]?\s*(\d{1,3})\b",
        r"\b(\d{1,3})\s*:\s*\d{1,3}\b",
    ]

    for pattern in numeric_patterns:
        match = re.search(pattern, text)
        if match:
            num = int(match.group(1))

            return {
                "surah_number": num,
                "matched_alias": str(num),
                "confidence": 0.98 if 1 <= num <= 114 else 1.0,
                "is_numeric": True,
                "is_valid": 1 <= num <= 114,
            }

    matches = []

    for surah_number, aliases in SURAH_ALIASES.items():
        for alias in aliases:
            alias_norm = normalize_text(alias)
            pattern = r"(?<!\w)" + re.escape(alias_norm) + r"(?!\w)"

            if re.search(pattern, text):
                matches.append((surah_number, alias_norm))

    if not matches:
        return None

    matches.sort(key=lambda item: len(item[1]), reverse=True)
    surah_number, alias = matches[0]

    return {
        "surah_number": surah_number,
        "matched_alias": alias,
        "confidence": 0.95,
        "is_numeric": False,
        "is_valid": True,
    }


def extract_ayah_number(text: str):
    text = normalize_text(text)

    patterns = [
        r"\b(?:ayat|ayah|a)\s*[:\-]?\s*(\d{1,3})\b",
        r"\b\d{1,3}\s*:\s*(\d{1,3})\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            num = int(match.group(1))
            if num > 0:
                return num

    return None


def parse_direct_quran_reference(user_message: str):
    """
    Deteksi direct Quran lookup.

    Contoh:
    - QS Al Baqarah 255
    - QS Al-Baqarah ayat 255
    - surat yasin ayat 1
    - quran 2:255
    - surah 112 ayat 1
    """
    text = normalize_text(user_message)

    has_quran_intent = any(k in text for k in [
        "qs", "q.s", "quran", "al quran", "surah", "surat", "ayat"
    ])

    if not has_quran_intent:
        return None

    surah = detect_surah(text)
    ayah_number = extract_ayah_number(text)

    # Fallback untuk pola "QS Al Baqarah 255" tanpa kata ayat
    if surah and not ayah_number:
        numbers = [int(n) for n in re.findall(r"\b\d{1,3}\b", text)]

        # Jika surah numerik, angka kedua adalah ayat.
        if surah.get("is_numeric") and len(numbers) >= 2:
            ayah_number = numbers[1]

        # Jika surah nama, angka pertama yang muncul biasanya ayat.
        elif not surah.get("is_numeric") and numbers:
            ayah_number = numbers[-1]

    if not surah or not ayah_number:
        return None

    return {
        "type": "quran",
        "surah_number": surah["surah_number"],
        "ayah_number": ayah_number,
        "confidence": surah["confidence"],
        "matched_alias": surah["matched_alias"],
        "is_valid_surah": surah.get("is_valid", True),
    }