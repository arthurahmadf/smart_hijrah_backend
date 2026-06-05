import json
import os
from django.conf import settings

# Cache supaya tidak baca file berulang kali
_quran_data = None

def get_quran_data():
    global _quran_data
    if _quran_data is None:
        json_path = os.path.join(settings.BASE_DIR, 'data', 'quran_uthmani.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            _quran_data = json.load(f)
    return _quran_data


def get_ayah_text(surah_number, ayah_number):
    """Ambil teks ayat berdasarkan nomor surah dan ayat"""
    quran = get_quran_data()
    surah = next((s for s in quran if s['id'] == surah_number), None)
    if not surah:
        return None
    verse = next((v for v in surah['verses'] if v['id'] == ayah_number), None)
    return verse['text'] if verse else None


def get_surah_name(surah_number):
    """Ambil nama surah (transliteration)"""
    quran = get_quran_data()
    surah = next((s for s in quran if s['id'] == surah_number), None)
    return surah['transliteration'] if surah else None


def get_all_ayahs():
    """Return semua ayat dalam format flat list"""
    quran = get_quran_data()
    result = []
    for surah in quran:
        for verse in surah['verses']:
            result.append({
                'surah_number': surah['id'],
                'surah_name': surah['transliteration'],
                'ayah_number': verse['id'],
                'ayah_text': verse['text'],
                'total_words': len(verse['text'].split()),
            })
    return result