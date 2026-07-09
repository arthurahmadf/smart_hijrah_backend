# main/utils_embedding/embedder.py
from sentence_transformers import SentenceTransformer
import numpy as np
import time 
# ===== LOAD MODEL SEKALI (CACHE) =====
MODEL_NAME = 'IslamQA/bge-m3-finetuned'
_model = None

def get_embedder():
    """Singleton: load model sekali saat pertama dipanggil"""
    global _model
    if _model is None:
        print("[EMBEDDER] Loading model...")
        _model = SentenceTransformer(MODEL_NAME)
        print("[EMBEDDER] Model ready!")
    return _model

def get_embedding(text):
    """Ubah teks menjadi vector (list of float)"""
    model = get_embedder()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()

def batch_get_embeddings(texts, batch_size=32):
    """Ubah banyak teks menjadi vector (lebih efisien)"""
    model = get_embedder()
    embeddings = model.encode(texts, normalize_embeddings=True, batch_size=batch_size)
    return [emb.tolist() for emb in embeddings]


# ===== WARMING UP (DI PANGGIL SAAT SERVER START) =====
def warmup():
    """
    Panggil fungsi ini saat server start untuk pre-load model.
    """
    print("[EMBEDDER] 🔥 Warming up model...")
    start = time.time()
    get_embedder()
    elapsed = time.time() - start
    print(f"[EMBEDDER] ✅ Model loaded in {elapsed:.2f}s")