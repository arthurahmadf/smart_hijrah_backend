## 📊 **Dokumentasi Perhitungan Skor Tilawah Assistant**

---

### 1. Ringkasan

Sistem penilaian Tilawah Assistant menggunakan **2 skor utama** yang saling melengkapi:

| Skor | Fungsi | Rentang |
|------|--------|---------|
| **Word Accuracy** | Mengukur ketepatan dan kelengkapan kata yang dibaca | 0-100% |
| **Tajwid Score** | Mengukur kualitas penerapan hukum tajwid | 0-100% |

**Keduanya berdiri sendiri**, namun `tajwid_score` menggunakan `word_accuracy` sebagai faktor penalti jika ada kesalahan kata.

---

### 2. Jenis Kesalahan Bacaan

Berdasarkan ilmu tajwid, kesalahan membaca Al-Qur'an dibagi menjadi dua kategori:

| Kategori | Definisi | Dampak |
|----------|----------|--------|
| **Lahn Jaliy (Fatal)** | Kesalahan pada kata/huruf yang mengubah makna | Word Accuracy turun signifikan |
| **Lahn Khafiy (Ringan)** | Kesalahan pada hukum tajwid (tidak mengubah makna) | Tajwid Score turun |

**Prinsip penilaian:**
- Jika ada kesalahan kata (Lahn Jaliy), maka bacaan secara otomatis berkurang nilainya (Word Accuracy turun)
- Jika kata benar tapi tajwid kurang (Lahn Khafiy), maka Tajwid Score turun

---

### 3. Word Accuracy (Akurasi Kata)

#### 3.1. Definisi
Word Accuracy adalah persentase kata yang dibaca **dengan benar dan lengkap** dibandingkan total kata dalam ayat referensi.

#### 3.2. Komponen
| Komponen | Definisi | Contoh |
|----------|----------|--------|
| **Correct** | Kata dibaca dengan benar | User baca `الرَّحْمَٰنِ` ✅ |
| **Wrong** | Kata dibaca salah | User baca `الرَّحِيمِ` → seharusnya `الرَّحْمَٰنِ` ❌ |
| **Missing** | Kata terlewat tidak dibaca | User skip 1 kata ❌ |
| **Extra** | Kata tambahan (tidak dihitung) | User baca kata di luar ayat (tidak mengurangi) |

#### 3.3. Rumus
```
Word Accuracy = (Correct / (Correct + Wrong + Missing)) × 100
```

#### 3.4. Contoh Kasus

| Skenario | Correct | Wrong | Missing | Total | Word Accuracy |
|----------|---------|-------|---------|-------|---------------|
| Semua kata benar | 10 | 0 | 0 | 10 | 100% |
| 8 benar, 2 salah | 8 | 2 | 0 | 10 | 80% |
| 7 benar, 3 terlewat | 7 | 0 | 3 | 10 | 70% |
| 6 benar, 2 salah, 2 terlewat | 6 | 2 | 2 | 10 | 60% |
| 0 benar | 0 | 10 | 0 | 10 | 0% |

---

### 4. Tajwid Score (Kualitas Tajwid)

#### 4.1. Definisi
Tajwid Score adalah persentase hukum tajwid yang **diterapkan dengan benar**, dengan penalti dari kesalahan kata.

#### 4.2. Komponen

**Tajwid Quality (Raw)**
- Total hukum tajwid yang **seharusnya** ada dalam ayat (dari Tajwid Engine)
- Total hukum tajwid yang **terdeteksi** (diterapkan dengan benar)

**Penalti Word Accuracy**
- Jika ada kesalahan kata (Lahn Jaliy), maka nilai tajwid dikurangi secara proporsional

#### 4.3. Rumus

```
Step 1: Tajwid Quality = (Detected Rules / Expected Rules) × 100
Step 2: Tajwid Score = Tajwid Quality × (Word Accuracy / 100)
```

#### 4.4. Contoh Kasus

| Skenario | Word Accuracy | Expected Rules | Detected Rules | Tajwid Quality | Tajwid Score |
|----------|---------------|----------------|----------------|----------------|--------------|
| Kata benar, semua tajwid benar | 100% | 5 | 5 | 100% | 100% |
| Kata benar, 3 dari 5 tajwid benar | 100% | 5 | 3 | 60% | 60% |
| Kata 80% benar, semua tajwid benar | 80% | 5 | 5 | 100% | 80% |
| Kata 80% benar, 3 dari 5 tajwid benar | 80% | 5 | 3 | 60% | 48% |

#### 4.5. Penjelasan Penalti

`Tajwid Score` dikalikan dengan `Word Accuracy` karena:

| Kondisi | Logika |
|---------|--------|
| Word Accuracy 100% | Tidak ada penalti, tajwid quality full |
| Word Accuracy 80% | Ada 20% kesalahan kata, tajwid mendapat penalti 20% |
| Word Accuracy 50% | Ada 50% kesalahan kata, tajwid mendapat penalti 50% |

**Jika kata salah (Lahn Jaliy), maka apapun tajwidnya, bacaan tidak bisa sempurna.**

---

### 5. Perbandingan Skor

| Aspek | Word Accuracy | Tajwid Score |
|-------|---------------|--------------|
| **Objek penilaian** | Kata yang dibaca | Hukum tajwid |
| **Kesalahan fatal (Lahn Jaliy)** | ❌ Menurunkan skor | ⚠️ Penalti melalui Word Accuracy |
| **Kesalahan ringan (Lahn Khafiy)** | ✅ Tidak terpengaruh | ❌ Menurunkan skor |
| **Kata terlewat** | ❌ Menurunkan skor | ⚠️ Penalti melalui Word Accuracy |
| **Kata tambahan (extra)** | ✅ Tidak dihitung | ✅ Tidak terpengaruh |

---

### 6. Contoh Skor dalam Response JSON

```json
{
    "success": true,
    "data": {
        "id": 1,
        "surah_name": "Al-Fatihah",
        "ayah_number": 1,
        "ayah": "بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ",
        "word_accuracy": 75.0,
        "tajwid_score": 60.0,
        "ai_feedback": [
            {
                "id": 1,
                "type": "correct",
                "arabic": "بِسۡمِ ٱللَّهِ",
                "caption": null
            },
            {
                "id": 2,
                "type": "correction",
                "arabic": "ٱلرَّحۡمَٰنِ",
                "caption": "Kata 'الرَّحِيمِ' seharusnya dibaca 'الرَّحۡمَٰنِ'. Nun mati bertemu huruf ر dibaca Idgham Bilaghunnah."
            }
        ]
    }
}
```

---

### 7. Interpretasi Skor untuk User

| Skor | Interpretasi |
|------|--------------|
| 90-100% | Sangat Baik — Bacaan hampir sempurna |
| 75-89% | Baik — Ada beberapa kesalahan kecil |
| 60-74% | Cukup — Perlu latihan lebih |
| 45-59% | Perlu Perbaikan — Banyak kata yang salah |
| 0-44% | Perlu Bimbingan — Sebaiknya belajar dengan guru |

---

### 8. Kode Implementasi

```python
def _calculate_scores(match_result, tajwid_result):
    """
    Hitung 2 skor terpisah:
    1. word_accuracy = (kata benar / total kata referensi) × 100
    2. tajwid_score = kualitas tajwid × word_accuracy
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
    
    # 2. Tajwid Quality (raw)
    total_expected = _count_expected_tajwid_rules(tajwid_result)
    detected = _count_detected_tajwid_rules(tajwid_result)
    
    if total_expected == 0:
        tajwid_quality = 0.0
    else:
        tajwid_quality = (detected / total_expected) * 100
    
    # 3. Tajwid Score = quality × accuracy (penalti)
    tajwid_score = (word_accuracy / 100) * tajwid_quality
    
    return {
        'word_accuracy': round(word_accuracy, 2),
        'tajwid_score': round(tajwid_score, 2)
    }
```

---

### 9. Validasi & Testing

| Test Case | Word Accuracy | Tajwid Quality | Tajwid Score | Status |
|-----------|---------------|----------------|--------------|--------|
| Semua kata benar, semua tajwid benar | 100% | 100% | 100% | ✅ |
| Semua kata benar, 50% tajwid benar | 100% | 50% | 50% | ✅ |
| 80% kata benar, semua tajwid benar | 80% | 100% | 80% | ✅ |
| 80% kata benar, 50% tajwid benar | 80% | 50% | 40% | ✅ |
| 0% kata benar | 0% | 100% | 0% | ✅ |
| Tidak ada hukum tajwid | 100% | 0% | 0% | ✅ |

---

**Dokumen ini untuk keperluan internal tim Smart Hijrah.** 🚀