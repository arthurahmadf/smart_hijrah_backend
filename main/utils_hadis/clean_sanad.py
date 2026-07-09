# main/utils_hadis/clean_sanad.py
import re

def clean_sanad_arab(text):
    """
    Hapus sanad dari teks Arab hadis.
    Contoh: "حَدَّثَنَا عَبْدُ اللَّهِ ... عَنِ النَّبِيِّ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ قَالَ..."
    → "قَالَ النَّبِيُّ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ..."
    """
    # Pola sanad: diawali dengan "حدثنا" atau "أخبرنا" atau "عن"
    # Kita cari bagian setelah "عن النبي" atau "أن النبي" atau langsung ke inti hadis
    
    # Cari pola "عَنِ النَّبِيِّ" atau "أَنَّ النَّبِيَّ"
    patterns = [
        r'عَنِ النَّبِيِّ[^.]*?',
        r'أَنَّ النَّبِيَّ[^.]*?',
        r'عَنْ رَسُولِ اللَّهِ[^.]*?',
        r'أَنَّ رَسُولَ اللَّهِ[^.]*?',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            # Ambil dari posisi match sampai akhir
            return text[match.start():]
    
    # Jika tidak ada pola, coba cari "قَالَ" atau "فَعَلَ" sebagai indikator inti hadis
    if ' قَالَ ' in text:
        idx = text.find(' قَالَ ')
        return text[idx:].strip()
    
    # Jika tidak ketemu, kembalikan teks asli
    return text


def clean_sanad_indonesian(text):
    """
    Hapus sanad dari terjemahan Indonesia.
    Contoh: "Telah menceritakan kepada kami [Abdullah...] bahwasanya Nabi..."
    → "Nabi shallallahu 'alaihi wasallam..."
    """
    # Cari pola "bahwasanya Nabi" atau "dari Nabi" atau langsung ke inti
    patterns = [
        r'bahwasanya Nabi[^.]*?',
        r'bahwa Nabi[^.]*?',
        r'dari Nabi[^.]*?',
        r'Rasulullah shallallahu[^.]*?',
        r'Nabi shallallahu[^.]*?',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return text[match.start():]
    
    # Jika tidak ketemu, cari "beliau" atau "rasulullah"
    if 'beliau' in text:
        idx = text.find('beliau')
        return text[idx:].strip()
    
    return text