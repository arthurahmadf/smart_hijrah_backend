# main/utils_hadis/search.py
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from main.models_hadis import Hadis, KitabHadis
import re


def search_hadis_by_keyword(query, limit=10):
    """
    Cari hadis berdasarkan kata kunci di teks + kitab + nomor
    """
    if not query:
        return []
    
    query_lower = query.lower()
    kitab_match = None
    nomor_match = None
    
    # ===== 1. DETEKSI KITAB (lebih fleksibel) =====
    all_kitab = KitabHadis.objects.all()
    
    for kitab in all_kitab:
        kitab_words = kitab.nama_indonesia.lower().split()
        # Cek apakah ada kata dari nama kitab yang muncul di query
        for word in kitab_words:
            if word in query_lower and len(word) > 2:
                kitab_match = kitab
                break
        if kitab_match:
            break
    
    # ===== 2. DETEKSI NOMOR =====
    number_pattern = r'nomor\s*(\d+)|no\.?\s*(\d+)'
    match = re.search(number_pattern, query_lower)
    if match:
        nomor_match = int(match.group(1) or match.group(2))
    
    # ===== 3. QUERY SPESIFIK (kitab + nomor) =====
    if kitab_match and nomor_match:
        results = Hadis.objects.filter(
            kitab=kitab_match,
            nomor=nomor_match
        )[:limit]
        if results:
            return list(results)
    
    # ===== 4. QUERY KITAB SAJA =====
    if kitab_match:
        results = Hadis.objects.filter(kitab=kitab_match)[:limit]
        if results:
            return list(results)
    
    # ===== 5. FULL-TEXT SEARCH =====
    search_query = SearchQuery(query, config='simple')
    results = Hadis.objects.filter(
        search_vector=search_query
    ).annotate(
        rank=SearchRank(
            SearchVector('teks_hadis', weight='A') +
            SearchVector('isi_hadis', weight='B'),
            search_query
        )
    ).filter(rank__gt=0.1).order_by('-rank')[:limit]
    
    if results:
        return list(results)
    
    return []