
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
TANWIN_DAMM_UTHMANI = '\u065e'
TANWIN_KASR_UTHMANI = '\u0656'
TANWIN_FATH_UTHMANI = '\u0657'
TANWIN = [TANWIN_FATH, TANWIN_KASR, TANWIN_DAMM, TANWIN_DAMM_UTHMANI, TANWIN_KASR_UTHMANI, TANWIN_FATH_UTHMANI]

MADDA_ABOVE = '\u0653'

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

# Idgham Mutajanisain — huruf yang makhrajnya sama tapi sifat berbeda
MUTAJANISAIN_PAIRS = [
    ('ت', 'د'), ('ت', 'ط'),
    ('د', 'ت'), ('د', 'ط'),
    ('ط', 'ت'), ('ط', 'د'),
    ('ث', 'ذ'), ('ث', 'ظ'),
    ('ذ', 'ث'), ('ذ', 'ظ'),
    ('ظ', 'ث'), ('ظ', 'ذ'),
    ('ب', 'م'), ('م', 'ب'),
    ('ل', 'ر'), ('ر', 'ل'),
]

# Idgham Mutaqaribain — huruf yang makhrajnya berdekatan
MUTAQARIBAIN_PAIRS = [
    ('ق', 'ك'), ('ك', 'ق'),
    ('ن', 'ل'), ('ن', 'ر'),
]

ALEF = '\u0627'
ALEF_UTHMANI = '\u0671'
ALEF_MADDA = '\u0622'
ALEF_WITH_HAMZA_ABOVE = '\u0623'
ALEF_WITH_HAMZA_BELOW = '\u0625'
ALEF_KHANJARIYAH = '\u0670'
ALL_ALEF = [ALEF, ALEF_UTHMANI, ALEF_MADDA, ALEF_WITH_HAMZA_ABOVE, ALEF_WITH_HAMZA_BELOW, ALEF_KHANJARIYAH]

WAW = '\u0648'
YA = '\u064a'
LAM = '\u0644'
NUN = '\u0646'
MIM = '\u0645'
HA = '\u0647'

# ===== KONSTANTA UNTUK ATURAN BARU =====
WAW_SUKUN = WAW
YA_SUKUN = YA
RA = '\u0631'
LAM_JALALAH = LAM
ALEF_JALALAH = ALEF

# Tanda waqaf
SAKTAH = '\u06db'

HAMZAH_LETTERS = ['ء', 'أ', 'إ', 'آ', 'ئ', 'ؤ']


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
        '\u065e', '\u0656', '\u0657', '\u0658', '\u065f',
        '\u0653', '\u0654', '\u0655', '\u0670',
    ]
    for h in harakat:
        text = text.replace(h, '')
    text = text.replace('\u0671', '\u0627')
    return text


def get_base_letter(char):
    return strip_harakat(char)


def make_rule(rule, name, description, severity, priority, for_levels):
    return {
        'rule': rule,
        'name': name,
        'description': description,
        'severity': severity,
        'priority': priority,
        'for_levels': for_levels
    }


# ===== RULE CHECKERS =====

def _classify_nun_mati(following_letter, is_tanwin=False):
    prefix = "Tanwin" if is_tanwin else "Nun mati"

    if following_letter in HALQI:
        return make_rule(
            'izhar_halqi', 'Izhar Halqi',
            f'{prefix} bertemu huruf {following_letter} (huruf halqi) dibaca jelas tanpa dengung.',
            'info', 1, ['basic', 'intermediate', 'expert']
        )
    elif following_letter in IDGHAM_GHUNNAH:
        return make_rule(
            'idgham_bighunnah', 'Idgham Bighunnah',
            f'{prefix} bertemu huruf {following_letter} dibaca lebur dengan dengung.',
            'info', 1, ['basic', 'intermediate', 'expert']
        )
    elif following_letter in IDGHAM_BILA_GHUNNAH:
        return make_rule(
            'idgham_bilaghunnah', 'Idgham Bilaghunnah',
            f'{prefix} bertemu huruf {following_letter} dibaca lebur tanpa dengung.',
            'info', 1, ['basic', 'intermediate', 'expert']
        )
    elif following_letter == IQLAB_LETTER:
        return make_rule(
            'iqlab', 'Iqlab',
            f'{prefix} bertemu huruf ب dibaca berubah menjadi mim dengan dengung.',
            'warning', 1, ['basic', 'intermediate', 'expert']
        )
    elif following_letter in IKHFA_LETTERS:
        return make_rule(
            'ikhfa_haqiqi', 'Ikhfa Haqiqi',
            f'{prefix} bertemu huruf {following_letter} dibaca samar dengan dengung.',
            'warning', 1, ['basic', 'intermediate', 'expert']
        )
    return None


def check_nun_mati_tanwin(words, word_index):
    rules = []
    word = words[word_index]
    next_word = words[word_index + 1] if word_index + 1 < len(words) else None
    chars = list(word)

    for i, char in enumerate(chars):
        next_char = chars[i + 1] if i + 1 < len(chars) else None

        if char == NUN and next_char == IQLAB_SIGN:
            rules.append(make_rule(
                'iqlab', 'Iqlab',
                'Nun mati bertemu huruf ب dibaca berubah menjadi mim dengan dengung.',
                'warning', 1, ['basic', 'intermediate', 'expert']
            ))
            continue

        if char == NUN and next_char in ALL_SUKUN:
            following = None
            if i + 2 < len(chars):
                following = get_base_letter(chars[i + 2])
            elif next_word:
                following = get_base_letter(next_word[0])
            if following:
                rule = _classify_nun_mati(following)
                if rule:
                    rules.append(rule)
            continue

        if char == NUN and next_char is None:
            if next_word:
                following = get_base_letter(next_word[0])
                if following:
                    rule = _classify_nun_mati(following)
                    if rule:
                        rules.append(rule)
            continue

        if char == NUN and next_char and next_char not in [FATHAH, KASRAH, DAMMAH, SHADDA] + ALL_SUKUN + TANWIN:
            following = get_base_letter(next_char)
            if following and following.strip():
                rule = _classify_nun_mati(following)
                if rule:
                    rules.append(rule)
            continue

        if char in TANWIN:
            if next_word:
                next_word_base = get_base_letter(next_word[0])
                if next_word_base:
                    rule = _classify_nun_mati(next_word_base, is_tanwin=True)
                    if rule:
                        rules.append(rule)

    return rules


def check_mim_mati(words, word_index):
    rules = []
    word = words[word_index]
    next_word = words[word_index + 1] if word_index + 1 < len(words) else None
    chars = list(word)

    def _classify_mim(following):
        if following == MIM:
            return make_rule(
                'idgham_mimi', 'Idgham Mimi',
                'Mim mati bertemu huruf م dibaca lebur dengan dengung.',
                'warning', 1, ['basic', 'intermediate', 'expert']
            )
        elif following == IQLAB_LETTER:
            return make_rule(
                'ikhfa_syafawi', 'Ikhfa Syafawi',
                'Mim mati bertemu huruf ب dibaca samar dengan dengung.',
                'warning', 1, ['basic', 'intermediate', 'expert']
            )
        elif following:
            return make_rule(
                'izhar_syafawi', 'Izhar Syafawi',
                f'Mim mati bertemu huruf {following} dibaca jelas.',
                'info', 1, ['basic', 'intermediate', 'expert']
            )
        return None

    for i, char in enumerate(chars):
        next_char = chars[i + 1] if i + 1 < len(chars) else None

        if char == MIM and next_char in ALL_SUKUN:
            following = None
            if i + 2 < len(chars):
                following = get_base_letter(chars[i + 2])
            elif next_word:
                following = get_base_letter(next_word[0])
            rule = _classify_mim(following)
            if rule:
                rules.append(rule)
            continue

        if char == MIM and next_char is None:
            if next_word:
                following = get_base_letter(next_word[0])
                rule = _classify_mim(following)
                if rule:
                    rules.append(rule)

    return rules


def check_qalqalah(word, is_last_word=False):
    rules = []
    chars = list(word)
    word_length = len(chars)

    for i, char in enumerate(chars):
        base_char = get_base_letter(char)
        if base_char not in QALQALAH_LETTERS:
            continue

        is_sukun = False
        is_kubra = False

        # Kasus 1: Sukun eksplisit setelah huruf qalqalah
        if i + 1 < word_length and chars[i + 1] in ALL_SUKUN:
            is_sukun = True
            remaining = chars[i+2:]
            remaining_meaningful = [c for c in remaining if get_base_letter(c).strip()]
            if not remaining_meaningful:
                is_kubra = True

        # Kasus 2: Huruf qalqalah di akhir kata
        elif i == word_length - 1:
            is_sukun = True
            is_kubra = True

        # Kasus 3: Huruf qalqalah di akhir ayat (waqaf)
        elif is_last_word and i == word_length - 1:
            is_sukun = True
            is_kubra = True

        # Kasus 4: Huruf qalqalah yang diikuti huruf konsonan
        elif i + 1 < word_length and chars[i+1] not in [FATHAH, KASRAH, DAMMAH, SHADDA] + ALL_SUKUN:
            is_sukun = True
            remaining = chars[i+1:]
            remaining_meaningful = [c for c in remaining if get_base_letter(c).strip()]
            if not remaining_meaningful:
                is_kubra = True

        if is_sukun:
            rule_name = 'qalqalah_kubra' if is_kubra else 'qalqalah_sugra'
            desc = 'kuat, di akhir ayat' if is_kubra else 'ringan, di tengah kata'
            rules.append(make_rule(
                rule_name,
                'Qalqalah Kubra' if is_kubra else 'Qalqalah Sugra',
                f'Huruf {base_char} berharakat sukun dibaca memantul ({desc}).',
                'info', 1, ['basic', 'intermediate', 'expert']
            ))

    return rules


def check_ghunnah(word):
    rules = []
    chars = list(word)

    for i, char in enumerate(chars):
        if char not in [MIM, NUN]:
            continue
        next_char = chars[i + 1] if i + 1 < len(chars) else None

        if next_char == SHADDA:
            rules.append(make_rule(
                'ghunnah', 'Ghunnah Musyaddadah',
                f'Huruf {char} bertasydid dibaca dengung selama 2 harakat.',
                'info', 1, ['basic', 'intermediate', 'expert']
            ))
            continue

        if next_char in [FATHAH, KASRAH, DAMMAH]:
            next_next_char = chars[i + 2] if i + 2 < len(chars) else None
            if next_next_char == SHADDA:
                rules.append(make_rule(
                    'ghunnah', 'Ghunnah Musyaddadah',
                    f'Huruf {char} bertasydid dibaca dengung selama 2 harakat.',
                    'info', 1, ['basic', 'intermediate', 'expert']
                ))

    return rules


def check_alif_lam(word):
    rules = []
    stripped = strip_harakat(word)

    LAFZUL_JALALAH = [
        'الله', 'ٱلله', 'لله',
        'والله', 'وٱلله', 'بالله', 'بٱلله',
        'فالله', 'فٱلله', 'كالله', 'كٱلله',
        'تالله', 'تٱلله',
    ]
    if stripped in LAFZUL_JALALAH:
        return []

    PREFIX = ['و', 'ب', 'ف', 'ك', 'ل']
    start = None
    if len(stripped) >= 2 and stripped[0] in ALL_ALEF:
        start = 0
    elif len(stripped) >= 3 and stripped[0] in PREFIX and stripped[1] in ALL_ALEF:
        start = 1

    if start is not None and start + 1 < len(stripped) and stripped[start + 1] == LAM:
        following = stripped[start + 2] if start + 2 < len(stripped) else None
        if following in SYAMSIAH:
            rules.append(make_rule(
                'alif_lam_syamsiah', 'Alif Lam Syamsiah',
                f'Alif lam bertemu huruf {following} (syamsiah), lam dibaca lebur.',
                'info', 1, ['basic', 'intermediate', 'expert']
            ))
        elif following in QAMARIAH:
            rules.append(make_rule(
                'alif_lam_qamariah', 'Alif Lam Qamariah',
                f'Alif lam bertemu huruf {following} (qamariah), lam dibaca jelas.',
                'info', 1, ['basic', 'intermediate', 'expert']
            ))

    return rules


def check_mad(word, next_word=None):
    rules = []
    chars = list(word)
    stripped_word = strip_harakat(word)
    word_length = len(chars)

    # Huruf Muqatha'ah
    has_madda = MADDA_ABOVE in word
    if has_madda and len(stripped_word) <= 3:
        rules.append(make_rule(
            'mad_lazim_mukhaffaf', 'Mad Lazim Mukhaffaf Harfi',
            'Huruf muqatha\'ah dibaca panjang 6 harakat.',
            'warning', 1, ['intermediate', 'expert']
        ))
        return rules

    # Mad Lazim Mukhaffaf Kalimi
    if 'ءَآلۡـَٰٔنَ' in word or 'ءَآلْـَٰٔنَ' in word:
        rules.append(make_rule(
            'mad_lazim_mukhaffaf', 'Mad Lazim Mukhaffaf Kalimi',
            'Mad lazim mukhaffaf kalimi, dibaca panjang 6 harakat.',
            'warning', 1, ['intermediate', 'expert']
        ))
        return rules

    processed_indices = set()

    for i, char in enumerate(chars):
        if i in processed_indices:
            continue

        next_char = chars[i + 1] if i + 1 < word_length else None
        is_mad = False
        mad_char_idx = None
        mad_letter = None

        # Pola 1: fathah + alif
        if char == FATHAH and next_char in ALL_ALEF:
            is_mad = True
            mad_char_idx = i + 1
            mad_letter = 'alif'
            processed_indices.update([i, i + 1])

        # Pola 2: Alef Madda
        elif char in [ALEF_MADDA]:
            is_mad = True
            mad_char_idx = i
            mad_letter = 'alif_madda'
            processed_indices.add(i)

        # Pola 3: dammah + waw
        elif char == DAMMAH and next_char == WAW:
            is_mad = True
            mad_char_idx = i + 1
            mad_letter = 'waw'
            processed_indices.update([i, i + 1])

        # Pola 4: kasrah + ya
        elif char == KASRAH and next_char == YA:
            is_mad = True
            mad_char_idx = i + 1
            mad_letter = 'ya'
            processed_indices.update([i, i + 1])

        # Pola 5: Ya di akhir kata (MAD ASLI)
        elif char == YA and i == word_length - 1:
            is_mad = True
            mad_char_idx = i
            mad_letter = 'ya_sukun'
            processed_indices.add(i)

        # Pola 6: Waw di akhir kata (MAD ASLI)
        elif char == WAW and i == word_length - 1:
            is_mad = True
            mad_char_idx = i
            mad_letter = 'waw_sukun'
            processed_indices.add(i)

        if not is_mad:
            continue

        # Ambil karakter setelah huruf mad
        after_idx = mad_char_idx + 1
        skip = [FATHAH, KASRAH, DAMMAH, TATWEEL, '\u0670', '\u0654', '\u0655']
        while after_idx < word_length and chars[after_idx] in skip:
            after_idx += 1

        after_char = chars[after_idx] if after_idx < word_length else None
        after_base = get_base_letter(after_char) if after_char else None

        # Mad Lazim Mutsaqqal
        has_tasydid = False
        temp_idx = after_idx
        while temp_idx < word_length and temp_idx < after_idx + 3:
            if temp_idx < word_length and chars[temp_idx] == SHADDA:
                has_tasydid = True
                break
            temp_idx += 1

        if has_tasydid:
            rules.append(make_rule(
                'mad_lazim_mutsaqqal', 'Mad Lazim Mutsaqqal',
                'Huruf mad diikuti tasydid, dibaca panjang 6 harakat.',
                'warning', 1, ['intermediate', 'expert']
            ))
            continue

        # Mad Lazim Mukhaffaf
        if after_char and after_char in ALL_SUKUN:
            rules.append(make_rule(
                'mad_lazim_mukhaffaf', 'Mad Lazim Mukhaffaf',
                'Huruf mad diikuti sukun, dibaca panjang 6 harakat.',
                'warning', 1, ['intermediate', 'expert']
            ))
            continue

        # Mad Wajib Muttasil
        if after_base and after_base in HAMZAH_LETTERS:
            rules.append(make_rule(
                'mad_wajib_muttasil', 'Mad Wajib Muttasil',
                'Huruf mad bertemu hamzah dalam satu kata, dibaca panjang 4-5 harakat.',
                'warning', 1, ['intermediate', 'expert']
            ))
            continue

        # Mad Jaiz Munfasil
        is_end_of_word = False
        if mad_char_idx == word_length - 1:
            is_end_of_word = True
        else:
            remaining = chars[mad_char_idx + 1:]
            remaining_meaningful = [c for c in remaining if get_base_letter(c).strip()]
            if not remaining_meaningful:
                is_end_of_word = True

        if mad_letter in ['waw_sukun', 'ya_sukun']:
            is_end_of_word = True

        if is_end_of_word and next_word:
            next_first = None
            for c in list(next_word):
                base = get_base_letter(c)
                if base.strip():
                    next_first = base
                    break

            if next_first and next_first in HAMZAH_LETTERS:
                rules = [r for r in rules if r.get('rule') != 'mad_asli']
                rules.append(make_rule(
                    'mad_jaiz_munfasil', 'Mad Jaiz Munfasil',
                    'Huruf mad bertemu hamzah di kata berikutnya, dibaca panjang 2-5 harakat.',
                    'info', 1, ['intermediate', 'expert']
                ))
                continue

        # Mad Jaiz Munfasil khusus untuk قُوا dan يَا
        if 'قُوا' in word or 'قُوَا' in word or 'يَا' in word:
            if next_word and next_word.startswith('أ'):
                rules = [r for r in rules if r.get('rule') != 'mad_asli']
                rules.append(make_rule(
                    'mad_jaiz_munfasil', 'Mad Jaiz Munfasil',
                    'Huruf mad bertemu hamzah di kata berikutnya, dibaca panjang 2-5 harakat.',
                    'info', 1, ['intermediate', 'expert']
                ))
                continue

        # Mad Asli
        existing_mad = any(r.get('rule') in ['mad_wajib_muttasil', 'mad_jaiz_munfasil', 
                                              'mad_lazim_mutsaqqal', 'mad_lazim_mukhaffaf'] 
                          for r in rules)
        if not existing_mad:
            rules.append(make_rule(
                'mad_asli', 'Mad Asli (Thabi\'i)',
                'Huruf mad dibaca panjang 2 harakat.',
                'info', 2, ['basic', 'intermediate', 'expert']
            ))

    return rules


def check_idgham_mutamatsilain(words, word_index):
    rules = []
    word = words[word_index]
    next_word = words[word_index + 1] if word_index + 1 < len(words) else None
    chars = list(word)

    for i, char in enumerate(chars):
        base_char = get_base_letter(char)
        if not base_char.strip():
            continue

        next_char = chars[i + 1] if i + 1 < len(chars) else None

        if next_char in ALL_SUKUN:
            following_idx = i + 2
            while following_idx < len(chars) and not get_base_letter(chars[following_idx]).strip():
                following_idx += 1
            following = get_base_letter(chars[following_idx]) if following_idx < len(chars) else None

            if following and following == base_char:
                rules.append(make_rule(
                    'idgham_mutamatsilain', 'Idgham Mutamatsilain',
                    f'Huruf {base_char} mati bertemu huruf {following} yang sama, dibaca lebur.',
                    'info', 2, ['intermediate', 'expert']
                ))
            elif following is None and next_word:
                next_first_base = None
                for c in list(next_word):
                    base = get_base_letter(c)
                    if base.strip():
                        next_first_base = base
                        break
                if next_first_base and next_first_base == base_char:
                    rules.append(make_rule(
                        'idgham_mutamatsilain', 'Idgham Mutamatsilain',
                        f'Huruf {base_char} mati bertemu huruf {next_first_base} yang sama, dibaca lebur.',
                        'info', 2, ['intermediate', 'expert']
                    ))
        else:
            remaining = chars[i + 1:]
            remaining_letters = [c for c in remaining if get_base_letter(c).strip()]
            if not remaining_letters and next_word:
                next_first_base = None
                for c in list(next_word):
                    base = get_base_letter(c)
                    if base.strip():
                        next_first_base = base
                        break
                if next_first_base and next_first_base == base_char:
                    rules.append(make_rule(
                        'idgham_mutamatsilain', 'Idgham Mutamatsilain',
                        f'Huruf {base_char} mati bertemu huruf {next_first_base} yang sama, dibaca lebur.',
                        'info', 2, ['intermediate', 'expert']
                    ))

    return rules


def check_idgham_mutajanisain(words, word_index):
    rules = []
    word = words[word_index]
    next_word = words[word_index + 1] if word_index + 1 < len(words) else None
    chars = list(word)

    for i, char in enumerate(chars):
        base_char = get_base_letter(char)
        if not base_char.strip():
            continue

        next_char = chars[i + 1] if i + 1 < len(chars) else None

        def check_pair(base, following):
            if (base, following) in MUTAJANISAIN_PAIRS:
                return make_rule(
                    'idgham_mutajanisain', 'Idgham Mutajanisain',
                    f'Huruf {base} mati bertemu huruf {following} (makhraj sama), dibaca lebur.',
                    'info', 2, ['intermediate', 'expert']
                )
            return None

        if next_char in ALL_SUKUN:
            following_idx = i + 2
            while following_idx < len(chars) and not get_base_letter(chars[following_idx]).strip():
                following_idx += 1
            following = get_base_letter(chars[following_idx]) if following_idx < len(chars) else None

            if following:
                rule = check_pair(base_char, following)
                if rule:
                    rules.append(rule)
            elif next_word:
                next_first_base = None
                for c in list(next_word):
                    base = get_base_letter(c)
                    if base.strip():
                        next_first_base = base
                        break
                if next_first_base:
                    rule = check_pair(base_char, next_first_base)
                    if rule:
                        rules.append(rule)
        else:
            remaining = chars[i + 1:]
            remaining_letters = [c for c in remaining if get_base_letter(c).strip()]
            if not remaining_letters and next_word:
                next_first_base = None
                for c in list(next_word):
                    base = get_base_letter(c)
                    if base.strip():
                        next_first_base = base
                        break
                if next_first_base:
                    rule = check_pair(base_char, next_first_base)
                    if rule:
                        rules.append(rule)

    return rules



def check_idgham_mutaqaribain(words, word_index):
    rules = []
    word = words[word_index]
    next_word = words[word_index + 1] if word_index + 1 < len(words) else None
    chars = list(word)
    word_length = len(chars)

    def check_pair(base, following):
        if (base, following) in MUTAQARIBAIN_PAIRS:
            return make_rule(
                'idgham_mutaqaribain', 'Idgham Mutaqaribain',
                f'Huruf {base} mati bertemu huruf {following} (makhraj berdekatan), dibaca lebur.',
                'info', 2, ['intermediate', 'expert']
            )
        return None

    for i, char in enumerate(chars):
        base_char = get_base_letter(char)
        if not base_char.strip():
            continue

        next_char = chars[i + 1] if i + 1 < word_length else None

        # Kasus A: sukun eksplisit + huruf berikutnya
        if next_char in ALL_SUKUN:
            following_idx = i + 2
            while following_idx < word_length and not get_base_letter(chars[following_idx]).strip():
                following_idx += 1
            following = get_base_letter(chars[following_idx]) if following_idx < word_length else None

            if following:
                rule = check_pair(base_char, following)
                if rule:
                    rules.append(rule)
            elif next_word:
                next_first = None
                for c in list(next_word):
                    b = get_base_letter(c)
                    if b.strip():
                        next_first = b
                        break
                if next_first:
                    rule = check_pair(base_char, next_first)
                    if rule:
                        rules.append(rule)

        # Kasus B: huruf berharakat + huruf berikutnya + shadda (dengan skip harakat)
        elif next_char and get_base_letter(next_char).strip():
            following = get_base_letter(next_char)
            if not following:
                continue

            # Cari shadda setelah huruf berikutnya (skip harakat vokal)
            shadda_search_idx = i + 2
            while shadda_search_idx < word_length and chars[shadda_search_idx] in [FATHAH, KASRAH, DAMMAH]:
                shadda_search_idx += 1
            following_has_shadda = (
                shadda_search_idx < word_length and 
                chars[shadda_search_idx] == SHADDA
            )

            if following_has_shadda:
                rule = check_pair(base_char, following)
                if rule:
                    rules.append(rule)

        # Kasus C: huruf terakhir kata (mati implisit) + kata berikutnya
        else:
            remaining = chars[i + 1:]
            remaining_letters = [c for c in remaining if get_base_letter(c).strip()]
            if not remaining_letters and next_word:
                next_first = None
                for c in list(next_word):
                    b = get_base_letter(c)
                    if b.strip():
                        next_first = b
                        break
                if next_first:
                    rule = check_pair(base_char, next_first)
                    if rule:
                        rules.append(rule)

    return rules



def check_mad_aridh_lissukun(word, is_last_word):
    if not is_last_word:
        return []

    rules = []
    chars = list(word)
    word_length = len(chars)

    # Ambil semua huruf bermakna dari belakang
    meaningful_chars = []
    for i in range(word_length - 1, -1, -1):
        base = get_base_letter(chars[i])
        if base.strip():
            meaningful_chars.append((i, chars[i]))

    if not meaningful_chars:
        return []

    # Cek huruf terakhir yang bermakna
    last_idx, last_char = meaningful_chars[0]
    second_last = meaningful_chars[1] if len(meaningful_chars) > 1 else (None, None)
    second_last_idx, second_last_char = second_last

    # Pola 1: huruf terakhir adalah alef/waw/ya (mad langsung di akhir)
    is_mad = False
    if last_char in ALL_ALEF:
        is_mad = True
    elif last_char == WAW:
        prev = chars[last_idx - 1] if last_idx > 0 else None
        if prev == DAMMAH or prev not in [FATHAH, KASRAH, DAMMAH]:
            is_mad = True
    elif last_char == YA:
        prev = chars[last_idx - 1] if last_idx > 0 else None
        if prev == KASRAH or prev not in [FATHAH, KASRAH, DAMMAH]:
            is_mad = True

    # Pola 2: huruf terakhir adalah konsonan biasa,
    # tapi huruf sebelumnya adalah huruf mad
    # Contoh: يَعۡلَمُونَ → waw sebelum nun, يَوۡمِئِذٍ → tidak
    if not is_mad and second_last_char is not None:
        if second_last_char == WAW:
            prev_of_waw = chars[second_last_idx - 1] if second_last_idx > 0 else None
            if prev_of_waw == DAMMAH:
                is_mad = True
        elif second_last_char == YA:
            prev_of_ya = chars[second_last_idx - 1] if second_last_idx > 0 else None
            if prev_of_ya == KASRAH:
                is_mad = True
        elif second_last_char in ALL_ALEF:
            is_mad = True

    if is_mad:
        rules.append(make_rule(
            'mad_aridh_lissukun', 'Mad Aridh Lissukun',
            'Huruf mad di akhir ayat saat waqaf, dibaca panjang 2-6 harakat.',
            'info', 1, ['intermediate', 'expert']
        ))

    return rules


def check_mad_lin(word, is_last_word=False):
    rules = []
    chars = list(word)
    word_length = len(chars)

    for i, char in enumerate(chars):
        if char not in [WAW_SUKUN, YA_SUKUN]:
            continue

        has_fathah_before = False
        if i > 0:
            prev_char = chars[i-1]
            if prev_char == FATHAH:
                has_fathah_before = True
            elif i > 1 and chars[i-2] == FATHAH and get_base_letter(chars[i-1]).strip():
                has_fathah_before = True

        if not has_fathah_before:
            continue

        after_idx = i + 1
        while after_idx < word_length and chars[after_idx] in [FATHAH, KASRAH, DAMMAH, SHADDA]:
            after_idx += 1

        if after_idx >= word_length:
            if is_last_word:
                rules.append(make_rule(
                    'mad_lin', 'Mad Lin',
                    'Huruf waw/ya sukun didahului fathah, dibaca panjang 2-6 harakat saat waqaf.',
                    'info', 1, ['intermediate', 'expert']
                ))
            continue

        after_char = chars[after_idx]
        after_base = get_base_letter(after_char)

        if after_base and after_base.strip():
            if not is_last_word:
                continue

        rules.append(make_rule(
            'mad_lin', 'Mad Lin',
            'Huruf waw/ya sukun didahului fathah, dibaca panjang 2-6 harakat.',
            'info', 1, ['intermediate', 'expert']
        ))

    return rules


def check_mad_iwad(word, is_last_word=False):
    if not is_last_word:
        return []

    rules = []
    chars = list(word)
    word_length = len(chars)

    for i, char in enumerate(chars):
        # Cek tanwin fath (semua variannya)
        if char in [TANWIN_FATH, TANWIN_FATH_UTHMANI]:
            # Cek apakah setelah tanwin ada alef (atau akhir kata)
            remaining_idx = i + 1
            while remaining_idx < word_length and chars[remaining_idx] in ALL_ALEF:
                remaining_idx += 1
            # Setelah tanwin+alef tidak ada huruf bermakna = akhir kata
            remaining = chars[remaining_idx:]
            remaining_meaningful = [c for c in remaining if get_base_letter(c).strip()]
            if not remaining_meaningful:
                rules.append(make_rule(
                    'mad_iwad', 'Mad Iwad',
                    'Tanwin fathah di akhir ayat/waqaf dibaca panjang 2 harakat.',
                    'info', 1, ['intermediate', 'expert']
                ))
                break

    return rules





def check_mad_silah(word, next_word=None):
    rules = []
    chars = list(word)
    word_length = len(chars)

    for i, char in enumerate(chars):
        if char != HA:
            continue

        has_harakat_before = False
        if i > 0:
            if chars[i-1] in [FATHAH, KASRAH, DAMMAH]:
                has_harakat_before = True
            elif i > 1 and chars[i-2] in [FATHAH, KASRAH, DAMMAH]:
                if get_base_letter(chars[i-1]).strip():
                    has_harakat_before = True

        if not has_harakat_before:
            continue

        after_idx = i + 1
        while after_idx < word_length and chars[after_idx] in [FATHAH, KASRAH, DAMMAH, SHADDA]:
            after_idx += 1

        if after_idx >= word_length and next_word:
            for c in list(next_word):
                base = get_base_letter(c)
                if base.strip():
                    if base in HAMZAH_LETTERS:
                        rules.append(make_rule(
                            'mad_silah_thawilah', 'Mad Silah Thawilah',
                            'Ha dhomir bertemu hamzah, dibaca panjang 4-5 harakat.',
                            'info', 1, ['intermediate', 'expert']
                        ))
                    else:
                        rules.append(make_rule(
                            'mad_silah_qasirah', 'Mad Silah Qasirah',
                            'Ha dhomir bertemu huruf hidup, dibaca panjang 2 harakat.',
                            'info', 1, ['intermediate', 'expert']
                        ))
                    break
        elif after_idx < word_length:
            after_char = chars[after_idx]
            after_base = get_base_letter(after_char)
            if after_base and after_base.strip():
                if after_base in HAMZAH_LETTERS:
                    rules.append(make_rule(
                        'mad_silah_thawilah', 'Mad Silah Thawilah',
                        'Ha dhomir bertemu hamzah, dibaca panjang 4-5 harakat.',
                        'info', 1, ['intermediate', 'expert']
                    ))
                else:
                    rules.append(make_rule(
                        'mad_silah_qasirah', 'Mad Silah Qasirah',
                        'Ha dhomir bertemu huruf hidup, dibaca panjang 2 harakat.',
                        'info', 1, ['intermediate', 'expert']
                    ))

    return rules


def check_ra_tafkhim_tarqiq(word):
    rules = []
    chars = list(word)
    word_length = len(chars)

    for i, char in enumerate(chars):
        if get_base_letter(char) != RA:
            continue

        ra_harakat = None
        is_sukun = False

        if i + 1 < word_length and chars[i+1] in [FATHAH, KASRAH, DAMMAH]:
            ra_harakat = chars[i+1]
        elif i + 1 < word_length and chars[i+1] in ALL_SUKUN:
            is_sukun = True
            if i > 0 and chars[i-1] in [FATHAH, KASRAH, DAMMAH]:
                ra_harakat = chars[i-1]
        elif not ra_harakat and i > 0 and chars[i-1] in [FATHAH, KASRAH, DAMMAH]:
            ra_harakat = chars[i-1]
        elif i == word_length - 1:
            if i > 0 and chars[i-1] in [FATHAH, KASRAH, DAMMAH]:
                ra_harakat = chars[i-1]
                is_sukun = True

        if is_sukun and i > 0 and chars[i-1] == YA_SUKUN:
            rules.append(make_rule(
                'tarqiq_ra', 'Tarqiq Ra',
                'Huruf Ra sukun setelah ya sukun dibaca tipis.',
                'info', 2, ['intermediate', 'expert']
            ))
            continue

        if is_sukun and i > 0 and chars[i-1] == WAW_SUKUN:
            if i > 1 and chars[i-2] in [FATHAH, DAMMAH]:
                rules.append(make_rule(
                    'tafkhim_ra', 'Tafkhim Ra',
                    'Huruf Ra sukun setelah waw sukun didahului fathah/dammah dibaca tebal.',
                    'info', 2, ['intermediate', 'expert']
                ))
                continue

        if ra_harakat in [FATHAH, DAMMAH]:
            rules.append(make_rule(
                'tafkhim_ra', 'Tafkhim Ra',
                'Huruf Ra dibaca tebal karena fathah/dammah.',
                'info', 2, ['intermediate', 'expert']
            ))
        elif ra_harakat == KASRAH:
            rules.append(make_rule(
                'tarqiq_ra', 'Tarqiq Ra',
                'Huruf Ra dibaca tipis karena kasrah.',
                'info', 2, ['intermediate', 'expert']
            ))

    return rules


def check_lam_jalalah(word):
    rules = []
    chars = list(word)
    word_length = len(chars)

    for i, char in enumerate(chars):
        if char not in ALL_ALEF:
            continue
        if i + 1 >= word_length or chars[i+1] != LAM:
            continue
        if i + 2 >= word_length:
            continue

        next_char = chars[i+2]
        is_allah = False

        if next_char == LAM or next_char == SHADDA:
            for j in range(i+3, min(i+6, word_length)):
                if get_base_letter(chars[j]) == HA:
                    is_allah = True
                    break

        if not is_allah:
            continue

        prev_harakat = None
        if i > 0 and chars[i-1] in [FATHAH, KASRAH, DAMMAH]:
            prev_harakat = chars[i-1]
        elif i > 1 and chars[i-2] in [FATHAH, KASRAH, DAMMAH]:
            if get_base_letter(chars[i-1]).strip():
                prev_harakat = chars[i-2]

        if prev_harakat in [FATHAH, DAMMAH]:
            rules.append(make_rule(
                'tafkhim_lam_jalalah', 'Tafkhim Lam Jalalah',
                'Lam pada lafadz Allah dibaca tebal karena didahului fathah/dammah.',
                'info', 2, ['intermediate', 'expert']
            ))
        elif prev_harakat == KASRAH:
            rules.append(make_rule(
                'tarqiq_lam_jalalah', 'Tarqiq Lam Jalalah',
                'Lam pada lafadz Allah dibaca tipis karena didahului kasrah.',
                'info', 2, ['intermediate', 'expert']
            ))
        else:
            rules.append(make_rule(
                'tafkhim_lam_jalalah', 'Tafkhim Lam Jalalah',
                'Lam pada lafadz Allah dibaca tebal.',
                'info', 2, ['intermediate', 'expert']
            ))
        break

    return rules


def check_waqaf_saktah(word):
    rules = []
    if SAKTAH in word:
        rules.append(make_rule(
            'saktah', 'Saktah',
            'Berhenti sejenak tanpa mengambil napas.',
            'info', 2, ['expert']
        ))
    return rules

def resolve_priority(rules):
    if not rules:
        return rules

    rule_names = [r['rule'] for r in rules]

    if 'mad_iwad' in rule_names:
        rules = [r for r in rules if r['rule'] not in ['mad_aridh_lissukun', 'mad_asli']]
        return rules

    # Mad aridh hanya override mad asli kalau for_levels-nya sama
    # Jangan hapus mad_asli kalau mad_aridh hanya untuk intermediate/expert
    if 'mad_aridh_lissukun' in rule_names:
        aridh_rule = next(r for r in rules if r['rule'] == 'mad_aridh_lissukun')
        # Hanya hapus mad_asli jika mad_aridh mencakup semua level
        # Karena mad_aridh hanya intermediate+, biarkan mad_asli tetap ada
        # untuk level basic
        pass  # tidak hapus mad_asli di sini

    mad_higher = ['mad_wajib_muttasil', 'mad_jaiz_munfasil',
                  'mad_lazim_mutsaqqal', 'mad_lazim_mukhaffaf']
    if any(m in rule_names for m in mad_higher):
        rules = [r for r in rules if r['rule'] != 'mad_asli']
        rule_names = [r['rule'] for r in rules]

    if 'mad_silah_qasirah' in rule_names or 'mad_silah_thawilah' in rule_names:
        rules = [r for r in rules if r['rule'] != 'mad_asli']
        rule_names = [r['rule'] for r in rules]

    if 'idgham_bighunnah' in rule_names:
        rules = [r for r in rules if r['rule'] not in ['idgham_mutamatsilain', 'idgham_mutaqaribain']]
        rule_names = [r['rule'] for r in rules]

    if 'idgham_bilaghunnah' in rule_names:
        rules = [r for r in rules if r['rule'] not in ['idgham_mutamatsilain', 'idgham_mutaqaribain']]
        rule_names = [r['rule'] for r in rules]

    if 'qalqalah_kubra' in rule_names and 'qalqalah_sugra' in rule_names:
        rules = [r for r in rules if r['rule'] != 'qalqalah_sugra']

    return rules


def filter_by_level(rules, user_level):
    if user_level not in ['basic', 'intermediate', 'expert']:
        return rules
    return [r for r in rules if user_level in r.get('for_levels', [])]


# ===== MAIN ANALYZER =====

def analyze_tajwid(ayah_text, user_level=None):
    words = ayah_text.split()
    results = []

    for i, word in enumerate(words):
        word_rules = []
        is_last_word = (i == len(words) - 1)
        next_word = words[i + 1] if i + 1 < len(words) else None

        word_rules.extend(check_nun_mati_tanwin(words, i))
        word_rules.extend(check_mim_mati(words, i))
        word_rules.extend(check_qalqalah(word, is_last_word))
        word_rules.extend(check_ghunnah(word))
        word_rules.extend(check_alif_lam(word))
        word_rules.extend(check_mad(word, next_word))
        word_rules.extend(check_mad_iwad(word, is_last_word))
        word_rules.extend(check_mad_aridh_lissukun(word, is_last_word))
        word_rules.extend(check_mad_lin(word, is_last_word))
        word_rules.extend(check_mad_silah(word, next_word))
        word_rules.extend(check_ra_tafkhim_tarqiq(word))
        word_rules.extend(check_lam_jalalah(word))
        word_rules.extend(check_idgham_mutamatsilain(words, i))
        word_rules.extend(check_idgham_mutajanisain(words, i))
        word_rules.extend(check_idgham_mutaqaribain(words, i))
        word_rules.extend(check_waqaf_saktah(word))

        word_rules = resolve_priority(word_rules)

        if user_level:
            word_rules = filter_by_level(word_rules, user_level)

        # Setelah filter level: kalau mad_aridh masih ada, hapus mad_asli
        rule_names = [r['rule'] for r in word_rules]
        if 'mad_aridh_lissukun' in rule_names:
            word_rules = [r for r in word_rules if r['rule'] != 'mad_asli']

        if word_rules:
            results.append({
                'word': word,
                'word_index': i,
                'rules': word_rules
            })

    return results

    