import re

# ===== UNICODE ARABIC =====
# Huruf-huruf halqi (untuk Izhar Halqi)
HALQI = ['ء', 'ه', 'ع', 'ح', 'غ', 'خ']

# Huruf Idgham (dengan ghunnah: ي ن م و | tanpa ghunnah: ل ر)
IDGHAM_GHUNNAH = ['ي', 'ن', 'م', 'و']
IDGHAM_BILA_GHUNNAH = ['ل', 'ر']

# Huruf Ikhfa (15 huruf)
IKHFA_LETTERS = ['ت', 'ث', 'ج', 'د', 'ذ', 'ز', 'س', 'ش', 'ص', 'ض', 'ط', 'ظ', 'ف', 'ق', 'ك']

# Huruf Iqlab
IQLAB_LETTER = ['ب']

# Qalqalah
QALQALAH_LETTERS = ['ق', 'ط', 'ب', 'ج', 'د']

# Unicode tanda baca
SUKUN = '\u0652'
TANWIN_FATH = '\u064b'
TANWIN_KASR = '\u064d'
TANWIN_DAMM = '\u064c'
SHADDA = '\u0651'
FATHAH = '\u064e'
KASRAH = '\u0650'
DAMMAH = '\u064f'
ALEF = '\u0627'
WAW = '\u0648'
YA = '\u064a'


def has_nun_mati_or_tanwin(text):
    """Deteksi kehadiran nun mati atau tanwin"""
    # Tanwin
    if any(c in text for c in [TANWIN_FATH, TANWIN_KASR, TANWIN_DAMM]):
        return True
    # Nun mati (nun + sukun)
    if 'ن' + SUKUN in text:
        return True
    return False


def detect_ikhfa(text):
    """Deteksi ikhfa haqiqi: nun mati/tanwin diikuti huruf ikhfa"""
    words = text.split()
    for i, word in enumerate(words):
        # Dalam satu kata
        for j in range(len(word) - 1):
            char = word[j]
            next_char = word[j + 1] if j + 1 < len(word) else ''
            # Nun mati
            if char == 'ن' and next_char == SUKUN:
                following = word[j + 2] if j + 2 < len(word) else ''
                if following in IKHFA_LETTERS:
                    return True
            # Tanwin
            if char in [TANWIN_FATH, TANWIN_KASR, TANWIN_DAMM]:
                if i + 1 < len(words):
                    next_word_first = words[i + 1][0] if words[i + 1] else ''
                    if next_word_first in IKHFA_LETTERS:
                        return True
    return False


def detect_idgham(text):
    """Deteksi idgham: nun mati/tanwin diikuti huruf idgham"""
    words = text.split()
    for i, word in enumerate(words):
        for j in range(len(word)):
            char = word[j]
            if char in [TANWIN_FATH, TANWIN_KASR, TANWIN_DAMM]:
                if i + 1 < len(words):
                    next_first = words[i + 1][0] if words[i + 1] else ''
                    if next_first in IDGHAM_GHUNNAH + IDGHAM_BILA_GHUNNAH:
                        return True
    return False


def detect_iqlab(text):
    """Deteksi iqlab: nun mati/tanwin diikuti huruf ba"""
    words = text.split()
    for i, word in enumerate(words):
        # Dalam kata
        for j in range(len(word) - 1):
            if word[j] == 'ن' and SUKUN in word[j:j+2]:
                following = word[j + 2] if j + 2 < len(word) else ''
                if following == 'ب':
                    return True
        # Antar kata
        for char in [TANWIN_FATH, TANWIN_KASR, TANWIN_DAMM]:
            if char in word:
                if i + 1 < len(words) and words[i + 1]:
                    if words[i + 1][0] == 'ب':
                        return True
    return False


def detect_qalqalah(text):
    """Deteksi qalqalah: huruf qalqalah berharakat sukun"""
    for i in range(len(text) - 1):
        if text[i] in QALQALAH_LETTERS and text[i + 1] == SUKUN:
            return True
    return False


def detect_mad(text):
    """Deteksi mad: alef, waw, ya sebagai mad"""
    # Mad asli sederhana (alef setelah fathah, waw setelah dammah, ya setelah kasrah)
    for i in range(len(text) - 1):
        if text[i] == FATHAH and text[i + 1] == ALEF:
            return True
        if text[i] == DAMMAH and text[i + 1] == WAW:
            return True
        if text[i] == KASRAH and text[i + 1] == YA:
            return True
    return False


def detect_ghunnah(text):
    """Deteksi ghunnah: mim atau nun bertasydid"""
    for i in range(len(text) - 1):
        if text[i] in ['م', 'ن'] and text[i + 1] == SHADDA:
            return True
    return False


def classify_level(ayah_text, word_count):
    """
    Klasifikasi level ayat berdasarkan kompleksitas tajwid dan panjang ayat.
    Return: 'basic' | 'intermediate' | 'expert'
    """
    has_ikhfa = detect_ikhfa(ayah_text)
    has_idgham = detect_idgham(ayah_text)
    has_iqlab = detect_iqlab(ayah_text)
    has_qalqalah = detect_qalqalah(ayah_text)
    has_mad = detect_mad(ayah_text)
    has_ghunnah = detect_ghunnah(ayah_text)

    intermediate_count = sum([
        has_ikhfa, has_idgham, has_iqlab,
        has_qalqalah, has_ghunnah
    ])

    # Expert: ayat panjang (>10 kata) ATAU banyak hukum tajwid kompleks
    if word_count > 10 or intermediate_count >= 3:
        return 'expert'

    # Intermediate: ada hukum tajwid menengah
    if intermediate_count >= 1 or has_mad:
        return 'intermediate'

    # Basic: ayat pendek tanpa hukum tajwid kompleks
    return 'basic'