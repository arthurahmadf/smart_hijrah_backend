# main/utils_hadis/semantic_search.py
from pgvector.django import CosineDistance
from main.models_hadis import Hadis
from main.models_tilawah import TilawahAyahPool
from main.utils_embedding.embedder import get_embedding

def semantic_search_hadis(query, limit=10, threshold=0.6):
    """Cari hadis berdasarkan kemiripan makna"""
    if not query:
        return []
    
    query_vector = get_embedding(query)
    
    results = Hadis.objects.filter(
        embedding__isnull=False
    ).annotate(
        distance=CosineDistance('embedding', query_vector)
    ).filter(
        distance__lt=threshold
    ).order_by('distance')[:limit]
    
    for result in results:
        result.similarity = 1 - result.distance
        result.source = 'hadis'
    
    return results

def semantic_search_quran(query, limit=10, threshold=0.6):
    """Cari ayat Quran berdasarkan kemiripan makna"""
    if not query:
        return []
    
    query_vector = get_embedding(query)
    
    results = TilawahAyahPool.objects.filter(
        embedding__isnull=False
    ).annotate(
        distance=CosineDistance('embedding', query_vector)
    ).filter(
        distance__lt=threshold
    ).order_by('distance')[:limit]
    
    for result in results:
        result.similarity = 1 - result.distance
        result.source = 'quran'
    
    return results