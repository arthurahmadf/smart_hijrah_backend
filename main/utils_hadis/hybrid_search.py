# main/utils_hadis/hybrid_search.py
import re
from main.utils_hadis.semantic_search import semantic_search_quran, semantic_search_hadis
from main.utils_hadis.search import search_hadis_by_keyword


def is_specific_query(query):
    """
    Deteksi apakah query meminta hal spesifik (nomor, kitab, ayat tertentu)
    """
    patterns = [
        r'nomor\s*\d+',           # "nomor 3"
        r'no\.?\s*\d+',           # "no. 3", "no 3"
        r'ayat\s*\d+',            # "ayat 255"
        r'surah\s*\d+',           # "surah 2"
        r'\d+\s*:',               # "2:255"
        r'hr\s*\.?\s*\w+',        # "HR Abu Daud"
        r'riwayat\s*\w+',         # "riwayat Muslim"
        r'abu daud',              # "abu daud"
        r'bukhari',               # "bukhari"
        r'muslim',                # "muslim"
        r'tirmidzi',              # "tirmidzi"
        r'nasai',                 # "nasai"
        r'ibnu majah',            # "ibnu majah"
        r'malik',                 # "malik"
        r'ahmad',                 # "ahmad"
        r'darimi',                # "darimi"
    ]
    query_lower = query.lower()
    for pattern in patterns:
        if re.search(pattern, query_lower):
            return True
    return False


def _format_results(results, limit=5):
    """Format hasil agar JSON serializable"""
    formatted = []
    for r in results[:limit]:
        # Deteksi source
        source = getattr(r, 'source', None)
        if not source:
            if hasattr(r, 'surah_name'):
                source = 'quran'
            elif hasattr(r, 'kitab'):
                source = 'hadis'
            else:
                source = 'unknown'
        
        # Ambil text
        text = getattr(r, 'isi_hadis', None) or getattr(r, 'ayah_translation', None) or getattr(r, 'ayah_text', '')
        arabic = getattr(r, 'teks_hadis', None) or getattr(r, 'ayah_text', '')
        
        # Kitab (convert ke string)
        kitab = None
        if hasattr(r, 'kitab') and r.kitab:
            kitab = str(r.kitab)
        
        item = {
            'source': source,
            'kitab': kitab,
            'nomor': getattr(r, 'nomor', None),
            'surah': getattr(r, 'surah_name', None),
            'ayah': getattr(r, 'ayah_number', None),
            'text': text[:500] if text else '',
            'arabic': arabic[:300] if arabic else '',
            'similarity': getattr(r, 'similarity', 0),
        }
        formatted.append(item)
    
    return formatted


def hybrid_search(query, limit=5):
    """
    Hybrid search dengan logika terpisah:
    - Query spesifik (nomor/kitab) → keyword search SAJA
    - Query umum → semantic search dulu, baru keyword
    """
    results = []
    
    # ===== KASUS 1: QUERY SPESIFIK =====
    if is_specific_query(query):
        # 1a. Coba keyword search di hadis
        keyword_results = search_hadis_by_keyword(query, limit=limit)
        if keyword_results:
            return _format_results(keyword_results, limit)
        
        # 1b. Jika keyword gagal, coba semantic sebagai fallback
        semantic_results = semantic_search_hadis(query, limit=limit, threshold=0.3)
        if semantic_results:
            return _format_results(semantic_results, limit)
        
        # 1c. Jika masih gagal, coba Quran
        quran_results = semantic_search_quran(query, limit=limit, threshold=0.3)
        if quran_results:
            return _format_results(quran_results, limit)
        
        return []
    
    # ===== KASUS 2: QUERY UMUM (natural language) =====
    # 2a. Prioritas Quran
    quran_results = semantic_search_quran(query, limit=5, threshold=0.5)
    if quran_results:
        results.extend(quran_results)
    
    # 2b. Jika Quran tidak ketemu, cari Hadis
    if not results:
        hadis_results = semantic_search_hadis(query, limit=5, threshold=0.5)
        if hadis_results:
            results.extend(hadis_results)
    
    # 2c. Jika semantic gagal, coba keyword
    if not results:
        keyword_results = search_hadis_by_keyword(query, limit=limit)
        if keyword_results:
            for r in keyword_results:
                r.source = 'hadis'
                r.similarity = 0.8
            results.extend(keyword_results)
    
    return _format_results(results, limit)