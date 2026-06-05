# ===== UNICODE CONSTANTS =====
SUKUN = '\u0652'
SUKUN_UTHMANI = '\u06e1'
ALL_SUKUN = [SUKUN, SUKUN_UTHMANI]

TANWIN_FATH = '\u064b'
TANWIN_KASR = '\u064d'
TANWIN_DAMM = '\u064c'
SHADDA = '\u0651'
FATHAH = '\u064e'
KASRAH = '\u0650'
DAMMAH = '\u064f'
TATWEEL = '\u0640'
TANWIN_DAMM_UTHMANI = '\u065e'  # ٞ
TANWIN_KASR_UTHMANI = '\u0656'  # ٖ

TANWIN = [TANWIN_FATH, TANWIN_KASR, TANWIN_DAMM, TANWIN_DAMM_UTHMANI, TANWIN_KASR_UTHMANI]

# ===== HURUF KATEGORISASI =====
HALQI = ['ء', 'ه', 'ع', 'ح', 'غ', 'خ', 'أ', 'إ', 'آ', 'ٱ']
IDGHAM_GHUNNAH = ['ي', 'ن', 'م', 'و']
IDGHAM_BILA_GHUNNAH = ['ل', 'ر']
IDGHAM_ALL = IDGHAM_GHUNNAH + IDGHAM_BILA_GHUNNAH
IKHFA_LETTERS = ['ت', 'ث', 'ج', 'د', 'ذ', 'ز', 'س', 'ش', 'ص', 'ض', 'ط', 'ظ', 'ف', 'ق', 'ك']
IQLAB_LETTER = 'ب'
IQLAB_SIGN = '\u06e2' 
QALQALAH_LETTERS = ['ق', 'ط', 'ب', 'ج', 'د']
SYAMSIAH = ['ت', 'ث', 'د', 'ذ', 'ر', 'ز', 'س', 'ش', 'ص', 'ض', 'ط', 'ظ', 'ل', 'ن']
QAMARIAH = ['ء', 'ب', 'غ', 'ح', 'ج', 'ك', 'و', 'خ', 'ف', 'ع', 'ق', 'ي', 'م', 'ه']

# Alef variants
ALEF = '\u0627'
ALEF_UTHMANI = '\u0671'
ALL_ALEF = [ALEF, ALEF_UTHMANI]

WAW = '\u0648'
YA = '\u064a'
LAM = '\u0644'
NUN = '\u0646'
MIM = '\u0645'


# ===== HELPER =====

def strip_harakat(text):
    harakat = [
        SUKUN, SUKUN_UTHMANI, TANWIN_FATH, TANWIN_KASR, TANWIN_DAMM,
        SHADDA, FATHAH, KASRAH, DAMMAH, TATWEEL,
        '\u0610', '\u0611', '\u0612', '\u0613', '\u0614',
        '\u0615', '\u0616', '\u0617', '\u0618', '\u0619',
        '\u061a', '\u06d6', '\u06d7', '\u06d8', '\u06d9',
        '\u06da', '\u06db', '\u06dc',
        '\u06df', '\u06e0', '\u06e2', '\u06e3', '\u06e4',
        '\u06e7', '\u06e8', '\u06ea', '\u06eb', '\u06ec', '\u06ed',
        '\u065e',  # tanwin damm Uthmani ٞ
        '\u0656',  # subscript kasrah Uthmani ٖ
        '\u0657',  # subscript alef Uthmani
        '\u0658',  # subscript noon Uthmani
        '\u065f',  # wavy hamza Uthmani
    ]
    for h in harakat:
        text = text.replace(h, '')
    return text


def get_base_letter(char):
    """Ambil huruf dasar tanpa harakat"""
    return strip_harakat(char)


# ===== RULE CHECKERS =====

def check_nun_mati_tanwin(words, word_index):
    """Cek hukum nun mati dan tanwin"""
    rules = []
    word = words[word_index]
    next_word = words[word_index + 1] if word_index + 1 < len(words) else None
    chars = list(word)

    for i, char in enumerate(chars):
        next_char = chars[i + 1] if i + 1 < len(chars) else None

        # Iqlab eksplisit via tanda iqlab Uthmani
        if char == NUN and next_char == IQLAB_SIGN:
            rules.append({
                'rule': 'iqlab',
                'name': 'Iqlab',
                'description': 'Nun mati bertemu huruf ب dibaca berubah menjadi mim dengan dengung.',
                'severity': 'warning'
            })
            continue

        # Nun mati eksplisit (ada sukun) — dalam kata atau akhir kata
        if char == NUN and next_char in ALL_SUKUN:
            following = get_base_letter(chars[i + 2]) if i + 2 < len(chars) else None
            if not following and next_word:
                following = get_base_letter(next_word[0])
            if following:
                rule = _classify_nun_mati(following)
                if rule:
                    rules.append(rule)

        # Nun mati implisit: nun di akhir kata tanpa harakat apapun
        if char == NUN and next_char is None:
            if next_word:
                following = get_base_letter(next_word[0])
                if following:
                    rule = _classify_nun_mati(following)
                    if rule:
                        rules.append(rule)

        # Tanwin → hukum berlaku ke kata berikutnya
        if char in TANWIN:
            if next_word:
                next_word_base = get_base_letter(next_word[0])
                if next_word_base:
                    rule = _classify_nun_mati(next_word_base, is_tanwin=True)
                    if rule:
                        rules.append(rule)

    return rules

def _classify_nun_mati(following_letter, is_tanwin=False):
    """Klasifikasi hukum nun mati/tanwin berdasarkan huruf berikutnya"""
    prefix = "Tanwin" if is_tanwin else "Nun mati"

    if following_letter in HALQI:
        return {
            'rule': 'izhar_halqi',
            'name': 'Izhar Halqi',
            'description': f'{prefix} bertemu huruf {following_letter} (huruf halqi) dibaca jelas tanpa dengung.',
            'severity': 'info'
        }
    elif following_letter in IDGHAM_GHUNNAH:
        return {
            'rule': 'idgham_bighunnah',
            'name': 'Idgham Bighunnah',
            'description': f'{prefix} bertemu huruf {following_letter} dibaca lebur dengan dengung.',
            'severity': 'info'
        }
    elif following_letter in IDGHAM_BILA_GHUNNAH:
        return {
            'rule': 'idgham_bilaghunnah',
            'name': 'Idgham Bilaghunnah',
            'description': f'{prefix} bertemu huruf {following_letter} dibaca lebur tanpa dengung.',
            'severity': 'info'
        }
    elif following_letter == IQLAB_LETTER:
        return {
            'rule': 'iqlab',
            'name': 'Iqlab',
            'description': f'{prefix} bertemu huruf ب dibaca berubah menjadi mim dengan dengung.',
            'severity': 'warning'
        }
    elif following_letter in IKHFA_LETTERS:
        return {
            'rule': 'ikhfa_haqiqi',
            'name': 'Ikhfa Haqiqi',
            'description': f'{prefix} bertemu huruf {following_letter} dibaca samar dengan dengung.',
            'severity': 'warning'
        }
    return None


def check_mim_mati(words, word_index):
    """Cek hukum mim mati"""
    rules = []
    word = words[word_index]
    next_word = words[word_index + 1] if word_index + 1 < len(words) else None
    chars = list(word)

    for i, char in enumerate(chars):
        next_char = chars[i + 1] if i + 1 < len(chars) else None

        if char == MIM and next_char in ALL_SUKUN:
            following = None
            if i + 2 < len(chars):
                following = get_base_letter(chars[i + 2])
            elif next_word:
                following = get_base_letter(next_word[0])

            if following == MIM:
                rules.append({
                    'rule': 'idgham_mimi',
                    'name': 'Idgham Mimi',
                    'description': 'Mim mati bertemu huruf م dibaca lebur dengan dengung.',
                    'severity': 'warning'
                })
            elif following == IQLAB_LETTER:
                rules.append({
                    'rule': 'ikhfa_syafawi',
                    'name': 'Ikhfa Syafawi',
                    'description': 'Mim mati bertemu huruf ب dibaca samar dengan dengung.',
                    'severity': 'warning'
                })
            else:
                if following:
                    rules.append({
                        'rule': 'izhar_syafawi',
                        'name': 'Izhar Syafawi',
                        'description': f'Mim mati bertemu huruf {following} dibaca jelas.',
                        'severity': 'info'
                    })
    return rules


def check_qalqalah(word):
    """Cek hukum qalqalah"""
    rules = []
    chars = list(word)
    for i, char in enumerate(chars):
        base = get_base_letter(char)
        next_char = chars[i + 1] if i + 1 < len(chars) else None

        if base in QALQALAH_LETTERS and next_char in ALL_SUKUN:
            is_kubra = i >= len(chars) - 3
            rules.append({
                'rule': 'qalqalah_kubra' if is_kubra else 'qalqalah_sugra',
                'name': 'Qalqalah Kubra' if is_kubra else 'Qalqalah Sugra',
                'description': f'Huruf {base} berharakat sukun dibaca memantul '
                               f'{"(kuat, di akhir kata)" if is_kubra else "(ringan, di tengah kata)"}.',
                'severity': 'info'
            })
    return rules


def check_ghunnah(word):
    """Cek ghunnah: mim atau nun bertasydid"""
    rules = []
    chars = list(word)
    for i, char in enumerate(chars):
        next_char = chars[i + 1] if i + 1 < len(chars) else None
        if char in [MIM, NUN] and next_char == SHADDA:
            rules.append({
                'rule': 'ghunnah',
                'name': 'Ghunnah Musyaddadah',
                'description': f'Huruf {char} bertasydid dibaca dengung selama 2 harakat.',
                'severity': 'info'
            })
    return rules


def check_alif_lam(word):
    rules = []
    stripped = strip_harakat(word)

    # Exception: lafzul jalalah dengan berbagai prefix
    LAFZUL_JALALAH = [
        'الله', 'ٱلله', 'لله',
        'والله', 'وٱلله',
        'بالله', 'بٱلله',
        'فالله', 'فٱلله',
        'كالله', 'كٱلله',
        'تالله', 'تٱلله',
    ]
    if stripped in LAFZUL_JALALAH:
        return []

    # Alif lam hanya valid di posisi 0 atau setelah prefix satu huruf (و ب ف ك ل)
    PREFIX = ['و', 'ب', 'ف', 'ك', 'ل']

    start = None
    if len(stripped) >= 2 and stripped[0] in ALL_ALEF:
        start = 0
    elif len(stripped) >= 3 and stripped[0] in PREFIX and stripped[1] in ALL_ALEF:
        start = 1

    if start is not None and start + 1 < len(stripped) and stripped[start + 1] == LAM:
        following = stripped[start + 2] if start + 2 < len(stripped) else None
        if following in SYAMSIAH:
            rules.append({
                'rule': 'alif_lam_syamsiah',
                'name': 'Alif Lam Syamsiah',
                'description': f'Alif lam bertemu huruf {following} (syamsiah), lam dibaca lebur.',
                'severity': 'info'
            })
        elif following in QAMARIAH:
            rules.append({
                'rule': 'alif_lam_qamariah',
                'name': 'Alif Lam Qamariah',
                'description': f'Alif lam bertemu huruf {following} (qamariah), lam dibaca jelas.',
                'severity': 'info'
            })
    return rules

def check_nun_mati_tanwin(words, word_index):
    """Cek hukum nun mati dan tanwin"""
    rules = []
    word = words[word_index]
    next_word = words[word_index + 1] if word_index + 1 < len(words) else None
    chars = list(word)

    for i, char in enumerate(chars):
        next_char = chars[i + 1] if i + 1 < len(chars) else None

        # Nun mati eksplisit (ada sukun)
        if char == NUN and next_char in ALL_SUKUN:
            following = get_base_letter(chars[i + 2]) if i + 2 < len(chars) else None
            if not following and next_word:
                following = get_base_letter(next_word[0])
            if following:
                rule = _classify_nun_mati(following)
                if rule:
                    rules.append(rule)

        # Nun mati implisit: nun di akhir kata tanpa harakat apapun
        if char == NUN and next_char is None:
            if next_word:
                following = get_base_letter(next_word[0])
                if following:
                    rule = _classify_nun_mati(following)
                    if rule:
                        rules.append(rule)

        # Tanwin → hukum berlaku ke kata berikutnya
        if char in TANWIN:
            if next_word:
                next_word_base = get_base_letter(next_word[0])
                if next_word_base:
                    rule = _classify_nun_mati(next_word_base, is_tanwin=True)
                    if rule:
                        rules.append(rule)

    return rules

# ===== MAIN ANALYZER =====

def analyze_tajwid(ayah_text):
    """
    Analisa seluruh ayat dan return semua hukum tajwid yang berlaku.

    Args:
        ayah_text: teks ayat dengan harakat lengkap

    Returns:
        list of {
            'word': str,
            'word_index': int,
            'rules': list
        }
    """
    words = ayah_text.split()
    results = []

    for i, word in enumerate(words):
        word_rules = []

        word_rules.extend(check_nun_mati_tanwin(words, i))
        word_rules.extend(check_mim_mati(words, i))
        word_rules.extend(check_qalqalah(word))
        word_rules.extend(check_ghunnah(word))
        word_rules.extend(check_alif_lam(word))

        if word_rules:
            results.append({
                'word': word,
                'word_index': i,
                'rules': word_rules
            })

    return results