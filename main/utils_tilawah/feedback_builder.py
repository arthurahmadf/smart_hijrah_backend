import uuid
from .word_matcher import match_words
from .tajwid_engine import analyze_tajwid


def build_feedback(ayah_text, transcript, user_level=None):
    # Step 1 — Word matching
    match_result = match_words(ayah_text, transcript)

    # Step 2 — Tajwid analysis dengan user_level
    tajwid_result = analyze_tajwid(ayah_text, user_level=user_level)

    # Step 3 — Build feedback items
    feedback_items = []
    feedback_id = 1

    segments = _build_segments(match_result['word_results'], tajwid_result)

    for segment in segments:
        item = {
            'id': feedback_id,
            'id_str': f'feedback_{feedback_id}',
            'type': segment['type'],
            'arabic': segment['arabic'],
            'caption': segment.get('caption'),
            'audio_url': None
        }
        feedback_items.append(item)
        feedback_id += 1

    # Step 4 — Hitung skor
    scores = _calculate_scores(match_result, tajwid_result)

    return {
        'tajwid_score': scores['tajwid_score'],
        'word_accuracy': scores['word_accuracy'],
        'ai_feedback': feedback_items
    }


def _build_caption(word_result, tajwid_rules, status):
    """Build caption untuk correction item"""
    captions = []

    # Caption karena salah baca
    if status == 'wrong':
        ref = word_result.get('reference', '')
        trans = word_result.get('transcript', '')
        if ref and trans:
            captions.append(f'Kata "{trans}" seharusnya dibaca "{ref}".')
        elif ref:
            captions.append(f'Kata "{ref}" tidak terbaca.')

    elif status == 'missing':
        ref = word_result.get('reference', '')
        if ref:
            captions.append(f'Kata "{ref}" terlewat.')

    # Tambahkan tajwid rules jika ada
    for rule in tajwid_rules:
        captions.append(rule['description'])

    return ' '.join(captions) if captions else None


def _calculate_scores(match_result, tajwid_result):
    """
    Hitung 2 skor terpisah:
    1. word_accuracy = (kata benar / total kata referensi) × 100
    2. tajwid_score = 
       - Jika ada expected rules: (detected / expected) × 100 × (word_accuracy / 100)
       - Jika tidak ada expected rules: word_accuracy
    """
    
    # 1. Word Accuracy
    total_ref_words = (
        match_result['correct_count'] +
        match_result['wrong_count'] +
        match_result['missing_count']
    )
    
    if total_ref_words == 0:
        word_accuracy = 0.0
    else:
        word_accuracy = (match_result['correct_count'] / total_ref_words) * 100
    
    # 2. Tajwid Quality (hanya rules yang signifikan, exclude mad_asli)
    total_expected = _count_expected_tajwid_rules(tajwid_result)
    detected = _count_detected_tajwid_rules(tajwid_result)
    
    # Jika tidak ada expected rules, nilai tajwid sempurna (tidak ada yang perlu dinilai)
    if total_expected == 0:
        tajwid_score = word_accuracy
    else:
        tajwid_quality = (detected / total_expected) * 100
        tajwid_score = (word_accuracy / 100) * tajwid_quality
    
    return {
        'word_accuracy': round(word_accuracy, 2),
        'tajwid_score': round(tajwid_score, 2)
    }


def _count_expected_tajwid_rules(tajwid_result):
    """
    Total hukum tajwid yang seharusnya ada dalam ayat
    Exclude mad_asli (karena default, bukan penilaian tajwid)
    """
    total = 0
    for word in tajwid_result:
        for rule in word.get('rules', []):
            if rule.get('rule') != 'mad_asli':
                total += 1
    return total


def _count_detected_tajwid_rules(tajwid_result):
    """
    Total hukum tajwid yang terdeteksi (exclude mad_asli)
    """
    total = 0
    for word in tajwid_result:
        for rule in word.get('rules', []):
            if rule.get('rule') != 'mad_asli':
                total += 1
    return total


def _build_segments(word_results, tajwid_result):
    """
    Bangun segmen feedback dari word results.
    - Kata correct yang berurutan digabung jadi satu blok 'correct'
    - Kata wrong/missing jadi blok 'correction' dengan caption tajwid
    """
    # Buat map: word_index → tajwid rules
    tajwid_map = {}
    for t in tajwid_result:
        tajwid_map[t['word_index']] = t['rules']

    segments = []
    current_correct = []
    word_index = 0

    for word_result in word_results:
        status = word_result['status']

        if status == 'correct':
            current_correct.append(word_result['reference'])
            word_index += 1

        elif status in ['wrong', 'missing']:
            # Flush correct segment dulu
            if current_correct:
                segments.append({
                    'type': 'correct',
                    'arabic': ' '.join(current_correct),
                    'caption': None
                })
                current_correct = []

            tajwid_rules = tajwid_map.get(word_index, [])
            caption = _build_caption(word_result, tajwid_rules, status)

            segments.append({
                'type': 'correction',
                'arabic': word_result['reference'] or '',
                'caption': caption
            })
            word_index += 1

        elif status == 'extra':
            pass

    # Flush sisa correct segment
    if current_correct:
        segments.append({
            'type': 'correct',
            'arabic': ' '.join(current_correct),
            'caption': None
        })

    return segments