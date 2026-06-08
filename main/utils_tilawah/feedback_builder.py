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

    tajwid_score = _calculate_tajwid_score(match_result, tajwid_result)

    return {
        'tajwid_score': tajwid_score,
        'word_accuracy': match_result['word_accuracy'],
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


def _calculate_tajwid_score(match_result, tajwid_result):
    """
    Hitung tajwid score berdasarkan:
    - Word accuracy (bobot 60%)
    - Kelengkapan baca (tidak ada missing/wrong) (bobot 40%)
    """
    word_accuracy = match_result['word_accuracy']
    total_words = (
        match_result['correct_count'] +
        match_result['wrong_count'] +
        match_result['missing_count']
    )
    error_count = match_result['wrong_count'] + match_result['missing_count']

    if total_words == 0:
        return 0

    completeness = ((total_words - error_count) / total_words) * 100

    tajwid_score = (word_accuracy * 0.6) + (completeness * 0.4)
    return round(tajwid_score, 2)

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