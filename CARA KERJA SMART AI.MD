# 🧠 **Smart AI - RAG + Hybrid Search: Rangkuman & Alur Detail**

---

## 1. 📌 **Tujuan Utama**
Membangun **sistem Smart AI** yang mampu:
- Menjawab pertanyaan Islami dengan **akurat** dan **berdasarkan dalil** (Al-Qur'an & Hadis)
- **Menghilangkan halusinasi** (LLM tidak mengarang rujukan)
- **Menangani pertanyaan ambigu/salah tulis** dengan cerdas
- **Tetap cepat** meskipun ada proses pencarian tambahan

---

## 2. 🧩 **Masalah yang Diselesaikan**

| Masalah | Solusi |
|---------|--------|
| LLM mengarang hadis/ayat | RAG (Retrieval-Augmented Generation) |
| LLM memberi nomor hadis yang salah | Ambil teks **langsung dari database**, bukan dari LLM |
| Pertanyaan ambigu/salah tulis | NLP preprocessing + spell correction + synonym mapping |
| "Muskim" → "Muslim" | Spell correction |
| "Nabi daud" → "Sunan Abu Daud" | Synonym mapping + context detection |
| Kata kunci umum mengganggu pencarian | Tokenisasi, stopword removal, pembobotan |
| "APBN" tidak relevan | Keyword weighting (bobot 0 untuk kata non-Islami) |
| Tidak ada dalil langsung | Cari dalil analogi (qiyas) atau jawab dengan prinsip umum |

---

## 3. 🗄️ **Data yang Dimiliki**

### 3.1. **Al-Qur'an** ✅
- **Model:** `TilawahAyahPool` (sudah ada)
- **Jumlah:** 6.236 ayat
- **Field:** teks Utsmani, terjemahan, transliterasi

### 3.2. **Hadis** 📦 (BARU)
- **Sumber:** 9 file JSON
  - `bukhari.json`, `muslim.json`, `abu-daud.json`, `tirmidzi.json`, `nasai.json`, `ibnu-majah.json`, `malik.json`, `ahmad.json`, `darimi.json`
- **Estimasi total:** ~67.000+ hadis
- **Struktur:** `{ "number": 1, "arab": "...", "id": "..." }`
- **Status:** Belum di-import ke database

**Yang perlu dilakukan:** Import hadis ke database, bersihkan sanad (untuk search), dan tambahkan indexing.

---

## 4. 🔧 **Arsitektur Smart AI (RAG + Hybrid Search)**

### 4.1. **Alur Lengkap**

```
┌─────────────────────────────────────────────────────────────┐
│                      USER BERTANYA                          │
│              "Tampilkan hadis riwayat muskim nomor 5"       │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              1. INPUT PROCESSING (NLP Pipeline)             │
├─────────────────────────────────────────────────────────────┤
│  • Tokenisasi          → ["tampilkan", "hadis", ...]       │
│  • Stopword Removal    → ["hadis", "riwayat", "muskim"]    │
│  • Stemming (Indonesia)→ ["hadis", "riwayat", "muskim"]   │
│  • Spell Correction    → "muskim" → "muslim"              │
│  • Keyword Weighting   → "muslim": 10, "nomor 5": 10      │
│  • Keyword Extraction  → ["muslim", "nomor 5"]            │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│         2. HYBRID SEARCH (Database Quran + Hadis)          │
├─────────────────────────────────────────────────────────────┤
│  2a. Keyword Search (BM25 / PostgreSQL tsvector)           │
│       → Cari literal "muslim" + "nomor 5" di database      │
│       → Dapat 10-20 kandidat dengan skor BM25              │
│                                                             │
│  2b. Semantic Search (Embedding + Cosine Similarity)       │
│       → Ubah pertanyaan jadi vector                         │
│       → Bandingkan dengan vector teks hadis/ayat            │
│       → Dapat 10-20 kandidat dengan skor semantic           │
│                                                             │
│  2c. Hybrid Ranking (Reciprocal Rank Fusion / RRF)         │
│       → Gabungkan peringkat dari kedua metode               │
│       → Urutkan ulang → ambil TOP 5 kandidat               │
│       → Filter: jika skor hybrid < threshold, anggap tidak ada│
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              3. LLM SEBAGAI PEMILIH (Reranker)             │
├─────────────────────────────────────────────────────────────┤
│  • Prompt ke LLM:                                           │
│    "Pertanyaan user: {query}                                │
│     Berikut 5 kandidat dari database: [1: ...]             │
│     Tugas: Pilih 1 yang paling relevan, atau 'TIDAK ADA'   │
│     Jangan buat rujukan baru."                             │
│                                                             │
│  • LLM Response: "PILIHAN: 2, ALASAN: paling sesuai..."    │
└─────────────────────────┬───────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    4. JAWABAN FINAL                         │
├─────────────────────────────────────────────────────────────┤
│  • Jika ada kandidat terpilih:                              │
│      → Tampilkan teks ASLI dari database                    │
│      → Tambahkan catatan jika ada koreksi                   │
│                                                             │
│  • Jika tidak ada kandidat:                                 │
│      → Jawab jujur: "Tidak ditemukan di database"           │
│                                                             │
│  • Jika pertanyaan di luar Islam:                           │
│      → Tolak dengan sopan (aturan nomor 4)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. 🛠️ **Komponen yang Perlu Dibangun**

### 5.1. **Database Hadis** (MODEL & IMPORT)
| Komponen | Keterangan |
|----------|------------|
| Model `KitabHadis` | Master kitab (Bukhari, Muslim, dll) |
| Model `Hadis` | `kitab`, `nomor`, `teks_arab`, `terjemahan`, `teks_hadis` (tanpa sanad), `isi_hadis` (tanpa sanad) |
| Indexing | Full-Text Search (`SearchVector`), pgvector (nanti) |
| Script Import | Baca 9 JSON, simpan ke database (67.000+ hadis) |

### 5.2. **NLP Pipeline** (PREPROCESSING)
| Komponen | Library | Fungsi |
|----------|---------|--------|
| Tokenisasi | `nltk` / split() | Pecah kalimat jadi kata |
| Stopword | `nltk.corpus.stopwords` | Hapus kata tidak penting |
| Stemming | `Sastrawi` | Ambil kata dasar ("berzakat" → "zakat") |
| Spell Correction | `pyspellchecker` / custom | Koreksi typo ("muskim" → "muslim") |
| Synonym Mapping | Custom dictionary | "nabi daud" → "abu daud" (konteks hadis) |
| Keyword Weighting | Custom dictionary + TF-IDF | Bobot kata Islami (zakat=10, guna=1) |

### 5.3. **Hybrid Search** (PENCARIAN)
| Komponen | Teknologi | Fungsi |
|----------|-----------|--------|
| Keyword Search | PostgreSQL `tsvector` | Cari literal kata kunci |
| Semantic Search | PostgreSQL `pgvector` | Cari berdasarkan makna (embedding) |
| Hybrid Rank | RRF (Reciprocal Rank Fusion) | Gabungkan peringkat kedua metode |
| Threshold | Minimal skor hybrid | Jika < threshold, anggap tidak ditemukan |

### 5.4. **LLM Reranker** (PEMILIH)
| Komponen | Keterangan |
|----------|------------|
| Model | Groq (sekarang) / Qwen3-4B-Islamic (nanti) |
| Peran | **Pemilih** kandidat terbaik, BUKAN pencipta rujukan |
| Prompt | 5 kandidat + perintah memilih + larangan membuat rujukan baru |

### 5.5. **Integrasi ke Smart AI Existing**
| Komponen | Keterangan |
|----------|------------|
| `fallback_ai_client.py` | Tambahkan logika deteksi → RAG → Groq (umum) |
| `rag_engine.py` (baru) | Fungsi pencarian + reranking |
| `hadis_search.py` (baru) | Query ke database hadis |
| `quran_search.py` (baru) | Query ke `TilawahAyahPool` |

---

## 6. 📊 **Alur Logika "Kapan Pakai RAG vs Groq Normal"**

```
User bertanya
     ↓
1. Deteksi: Apakah pertanyaan butuh dalil spesifik?
   - Ada keyword: "hadis", "riwayat", "HR", "surat", "ayat", "nomor"
   - Ada nama kitab: "bukhari", "muslim", "abu daud", dll
   - Ada topik fiqih: "zakat", "sholat", "puasa", dll
     ↓
   YES              NO
     ↓               ↓
  2. RAG Engine   3. Groq Normal
     ↓               ↓
  - Hybrid Search  - Jawaban cepat
  - LLM Reranker   - Tanpa dalil
  - Jawaban+d
alil
     ↓               ↓
     └───────┬───────┘
             ▼
     Jawaban Final ke User
```

**Catatan:** Untuk pertanyaan yang butuh dalil, RAG selalu dijalankan. Groq normal hanya untuk percakapan umum (doa, motivasi, dll).

---

## 7. 🧪 **Contoh Skenario & Output**

### Skenario 1: "Tampilkan hadis riwayat muslim nomor 5"

| Tahap | Hasil |
|-------|-------|
| **NLP** | Keyword: ["muslim", "nomor 5"] |
| **Search** | Dapat TOP 5, salah satunya HR. Muslim No. 5 |
| **LLM Reranker** | Pilih HR. Muslim No. 5 |
| **Output** | Teks hadis ASLI dari database + nomor + kitab |

### Skenario 2: "Tampilkan hadist nabi daud"

| Tahap | Hasil |
|-------|-------|
| **NLP** | Keyword: ["hadis", "nabi", "daud"] |
| **Search** | Tidak ditemukan (0 hasil) |
| **Synonym** | "daud" → "abu daud" (deteksi konteks hadis) |
| **Search Ulang** | Dapat TOP 5 dari Sunan Abu Daud |
| **LLM Reranker** | Pilih salah satu + konfirmasi ke user |
| **Output** | "Tidak ada hadis dari Nabi Daud. Mungkin maksud Anda Sunan Abu Daud? Berikut salah satunya..." |

### Skenario 3: "Presiden berzakat menggunakan APBN"

| Tahap | Hasil |
|-------|-------|
| **NLP** | Keyword: ["zakat"], abaikan ["presiden", "apbn"] |
| **Search** | Dapat TOP 5 tentang zakat + niat |
| **LLM Reranker** | Pilih HR. Muslim No. 1010 (niat) + QS. At-Taubah: 103 |
| **Output** | "Berikut prinsip zakat dalam Islam... (disclaimer: tidak ada dalil tentang APBN)" |

### Skenario 4: "Apa itu black hole?"

| Tahap | Hasil |
|-------|-------|
| **NLP** | Keyword: ["black hole"] → tidak ditemukan di kamus Islami |
| **Search** | Tidak ada hasil |
| **Deteksi** | Pertanyaan di luar Islam |
| **Output** | "Maaf, saya adalah asisten khusus untuk pertanyaan seputar Islam..." |

---

## 8. 🗂️ **Database Hadis: Struktur Final**

### 8.1. Model `KitabHadis`
```python
nama          # 'abu-daud'
nama_indonesia # 'Sunan Abu Daud'
```

### 8.2. Model `Hadis`
```python
kitab         # ForeignKey ke KitabHadis
nomor         # 1, 2, 3, ...
teks_arab     # Lengkap dengan sanad (untuk display)
teks_hadis    # Tanpa sanad (untuk search)
terjemahan    # Lengkap dengan sanad (untuk display)
isi_hadis     # Tanpa sanad (untuk search)
search_vector # PostgreSQL tsvector (untuk keyword search)
embedding     # Vector (untuk semantic search, nanti)
```

### 8.3. **Proses Import**
1. Baca 9 file JSON
2. Parse `number`, `arab`, `id`
3. Bersihkan sanad dari `arab` → `teks_hadis`
4. Bersihkan sanad dari `id` → `isi_hadis`
5. Simpan ke database

---

## 9. 🔧 **Dependencies & Tools**

| Komponen | Library/Tools | Fungsi |
|----------|---------------|--------|
| NLP | `Sastrawi`, `nltk` | Stemming, stopword |
| Search | `django.contrib.postgres.search` | Full-Text Search |
| Semantic | `pgvector` (PostgreSQL extension) | Vector search |
| Embedding | `sentence-transformers` (model multilingual) | Ubah teks ke vector |
| LLM | Groq (sekarang), Qwen3-4B-Islamic (nanti) | Reranker |
| Spell Check | `pyspellchecker` atau custom | Koreksi typo |

---

## 10. 🚀 **Roadmap Implementasi**

| Fase | Tugas | Estimasi |
|------|-------|----------|
| **1** | Setup database hadis (model + import) | 1-2 hari |
| **2** | Setup PostgreSQL Full-Text Search | 1 hari |
| **3** | Setup pgvector (PostgreSQL extension) | 1 hari |
| **4** | NLP Pipeline (Sastrawi + stopword + weighting) | 2 hari |
| **5** | Hybrid Search (keyword + semantic) | 2-3 hari |
| **6** | LLM Reranker (integrasi ke Groq) | 1-2 hari |
| **7** | Integrasi ke Smart AI (RAG vs Groq normal) | 1-2 hari |
| **8** | Testing & validasi (50-100 sample) | 2-3 hari |
| **Total** | | **~10-14 hari** |

---

## 11. ✅ **Ringkasan Final**

| Komponen | Status | Keterangan |
|----------|--------|------------|
| Data Quran | ✅ Siap | `TilawahAyahPool` (6.236 ayat) |
| Data Hadis | 📦 Siap import | 9 file JSON (~67.000 hadis) |
| NLP Pipeline | 🔧 Perlu dibuat | Tokenisasi, stemming, weighting |
| Hybrid Search | 🔧 Perlu dibuat | Keyword + Semantic + RRF |
| LLM Reranker | 🔧 Perlu dibuat | Groq sebagai pemilih |
| Smart AI Existing | ✅ Siap | `fallback_ai_client.py` (akan diintegrasikan) |

---

**Dengan arsitektur ini, Smart AI akan:**
- ✅ Akurat (dalil dari database terverifikasi)
- ✅ Bebas halusinasi (LLM hanya memilih, bukan mencipta)
- ✅ Cepat (hybrid search + LLM ringan)
- ✅ Tahan banting (menangani typo, salah tulis, pertanyaan ambigu)