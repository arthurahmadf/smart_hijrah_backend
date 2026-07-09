# main/utils_nlp/processor.py
import re
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from .weights import ISLAMIC_WEIGHTS, GENERIC_WEIGHTS, STOPWORDS_CUSTOM

# ===== INISIALISASI =====
factory = StemmerFactory()
stemmer = factory.create_stemmer()

# Stopword NLTK (bahasa Indonesia)
try:
    STOPWORDS_NLTK = set(stopwords.words('indonesian'))
except:
    # Fallback jika NLTK belum download
    STOPWORDS_NLTK = set()

# Gabungkan stopword
STOPWORDS = STOPWORDS_NLTK.union(STOPWORDS_CUSTOM)

# ===== FUNGSI =====

def tokenize(text):
    """Tokenisasi teks menjadi list kata"""
    # Hapus tanda baca
    text = re.sub(r'[^\w\s]', ' ', text)
    # Pecah menjadi kata
    return text.lower().split()

def remove_stopwords(tokens):
    """Hapus kata stopword"""
    return [w for w in tokens if w not in STOPWORDS and len(w) > 2]

def stem_tokens(tokens):
    """Stemming (ambil kata dasar)"""
    return [stemmer.stem(w) for w in tokens]

def weight_keywords(tokens):
    """Beri bobot pada setiap kata"""
    weighted = {}
    for token in tokens:
        if token in ISLAMIC_WEIGHTS:
            weighted[token] = ISLAMIC_WEIGHTS[token]
        elif token in GENERIC_WEIGHTS:
            weighted[token] = GENERIC_WEIGHTS[token]
        else:
            weighted[token] = 0
    return weighted

def extract_keywords(text, limit=3):
    """
    Ekstrak kata kunci dari teks.
    Return: list of (keyword, weight) sorted by weight desc
    """
    # Tokenisasi
    tokens = tokenize(text)
    
    # Stemming
    stemmed = stem_tokens(tokens)
    
    # Weighting
    weighted = weight_keywords(stemmed)
    
    # Filter bobot > 0
    keywords = [(w, s) for w, s in weighted.items() if s > 0]
    
    # Urutkan berdasarkan bobot (descending)
    keywords.sort(key=lambda x: x[1], reverse=True)
    
    return keywords[:limit]

def extract_search_keywords(text, limit=3):
    """
    Ekstrak kata kunci untuk pencarian di database.
    Return: list of keywords (string)
    """
    
    keywords = extract_keywords(text, limit)
    return [k for k, w in keywords if w > 1]  # <-- Hanya ambil bobot > 1


def get_keyword_weight(text):
    """
    Dapatkan bobot rata-rata untuk suatu teks.
    Digunakan untuk menentukan apakah perlu RAG atau tidak.
    """
    tokens = tokenize(text)
    stemmed = stem_tokens(tokens)
    weighted = weight_keywords(stemmed)
    
    scores = [s for s in weighted.values() if s > 0]
    if not scores:
        return 0
    
    return sum(scores) / len(scores)