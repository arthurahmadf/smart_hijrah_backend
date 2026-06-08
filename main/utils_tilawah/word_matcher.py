import re
import unicodedata

# ===== NORMALISASI =====


def normalize_arabic(text):
    if not text:
        return ""

    # Hapus harakat (termasuk Uthmani variants)
    harakat = re.compile(
        r'[\u0610-\u061A\u064B-\u065F'
        r'\u0670\u06D6-\u06DC\u06DF-\u06E4'
        r'\u06E7\u06E8\u06EA-\u06ED'
        r'\u06e1\u0657\u0656\u065e\u065f'
        r'\u0653\u0654\u0655]'
    )
    text = harakat.sub('', text)

    # Normalize semua alef variants → ا
    text = re.sub(r'[أإآٱٲٳ\u0622\u0623\u0625\u0671]', 'ا', text)

    # Normalize alef maqsura → ya
    text = re.sub(r'ى', 'ي', text)

    # Normalize ta marbuta → ha
    text = re.sub(r'ة', 'ه', text)

    # Hapus tatweel
    text = re.sub(r'\u0640', '', text)

    # ===== KUNCI: Hapus alef yang berfungsi sebagai mad =====
    # Alef setelah huruf (bukan di awal kata) sering ditulis di standar
    # tapi tidak di Uthmani — hapus dari keduanya
    text = re.sub(r'(?<=[^\s])ا', '', text)

    # Hapus spasi berlebih
    text = ' '.join(text.split())

    return text.strip()

def split_to_words(text):
    """Split teks Arab menjadi list kata, hapus kata kosong"""
    return [w for w in text.split() if w.strip()]


# ===== WORD MATCHING =====

def match_words(reference_text, transcript_text):
    """
    Bandingkan teks referensi Quran dengan hasil transkripsi Whisper.
    
    Args:
        reference_text: teks ayat dari database (dengan harakat)
        transcript_text: hasil transkripsi Whisper (mungkin tanpa harakat)
    
    Returns:
        dict: {
            'word_results': list of word comparison results,
            'correct_count': int,
            'wrong_count': int,
            'missing_count': int,
            'extra_count': int,
            'word_accuracy': float (0-100)
        }
    """
    ref_words = split_to_words(reference_text)
    trans_words = split_to_words(transcript_text)

    ref_normalized = [normalize_arabic(w) for w in ref_words]
    trans_normalized = [normalize_arabic(w) for w in trans_words]

    # Gunakan algoritma LCS (Longest Common Subsequence) untuk matching
    word_results = _align_words(ref_words, trans_words, ref_normalized, trans_normalized)

    correct = sum(1 for r in word_results if r['status'] == 'correct')
    wrong = sum(1 for r in word_results if r['status'] == 'wrong')
    missing = sum(1 for r in word_results if r['status'] == 'missing')
    extra = sum(1 for r in word_results if r['status'] == 'extra')

    total_ref = len(ref_words)
    word_accuracy = round((correct / total_ref * 100), 2) if total_ref > 0 else 0

    return {
        'word_results': word_results,
        'correct_count': correct,
        'wrong_count': wrong,
        'missing_count': missing,
        'extra_count': extra,
        'word_accuracy': word_accuracy
    }


def _align_words(ref_words, trans_words, ref_norm, trans_norm):
    """
    Align kata referensi dengan kata transkripsi menggunakan DP alignment.
    Mirip dengan diff algorithm — deteksi correct, wrong, missing, extra.
    """
    n = len(ref_norm)
    m = len(trans_norm)

    # Build DP table untuk LCS
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref_norm[i-1] == trans_norm[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])

    # Traceback untuk dapatkan alignment
    results = []
    i, j = n, m
    aligned = []

    while i > 0 or j > 0:
        if i > 0 and j > 0 and ref_norm[i-1] == trans_norm[j-1]:
            aligned.append(('correct', ref_words[i-1], trans_words[j-1]))
            i -= 1
            j -= 1
        elif j > 0 and (i == 0 or dp[i][j-1] >= dp[i-1][j]):
            aligned.append(('extra', None, trans_words[j-1]))
            j -= 1
        else:
            aligned.append(('missing', ref_words[i-1], None))
            i -= 1

    aligned.reverse()

    # Convert ke format hasil — gabungkan missing+extra yang berdekatan jadi 'wrong'
    results = _merge_wrong(aligned)

    return results


def _merge_wrong(aligned):
    """
    Gabungkan pasangan missing+extra yang berdekatan menjadi 'wrong'.
    Contoh: user baca 'الرحيم' tapi harusnya 'الرحمن' → status 'wrong'
    """
    results = []
    i = 0
    while i < len(aligned):
        status, ref_word, trans_word = aligned[i]

        if status == 'missing' and i + 1 < len(aligned) and aligned[i+1][0] == 'extra':
            # Gabungkan jadi wrong
            results.append({
                'status': 'wrong',
                'reference': ref_word,
                'transcript': aligned[i+1][2],
            })
            i += 2
        elif status == 'extra' and i + 1 < len(aligned) and aligned[i+1][0] == 'missing':
            results.append({
                'status': 'wrong',
                'reference': aligned[i+1][1],
                'transcript': trans_word,
            })
            i += 2
        else:
            results.append({
                'status': status,
                'reference': ref_word,
                'transcript': trans_word,
            })
            i += 1

    return results