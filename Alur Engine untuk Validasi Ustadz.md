## ✅ **24 Hukum Tajwid yang Dideteksi Engine**

---

### **1. Izhar Halqi**
- **Deteksi:** Cari huruf nun mati (`نْ` atau `نۡ`) atau tanwin (`ً ٍ ٌ`) yang diikuti salah satu huruf halqi: `ء ه ع ح غ خ`
- **Contoh:** `مِنْ عِلْمٍ` → nun mati + `ع`
- **Dalil:** Surat An-Nisa ayat 11-12

---

### **2. Idgham Bighunnah**
- **Deteksi:** Cari nun mati/tanwin yang diikuti 4 huruf: `ي ن م و`
- **Contoh:** `مِن يَقُولُ` → nun mati + `ي`
- **Catatan:** Untuk `ن` dan `م` yang diikuti huruf sama, jika ada tasydid, lebih prioritas idgham bighunnah daripada mutamatsilain

---

### **3. Idgham Bilaghunnah**
- **Deteksi:** Cari nun mati/tanwin yang diikuti 2 huruf: `ل ر`
- **Contoh:** `مِن لَّدُنْهُ` → nun mati + `ل`

---

### **4. Iqlab**
- **Deteksi:** Cari nun mati/tanwin yang diikuti huruf `ب`, atau tanda iqlab `ۢ`
- **Contoh:** `مِنۢ بَعْدِ` → tanda iqlab + `ب`

---

### **5. Ikhfa Haqiqi**
- **Deteksi:** Cari nun mati/tanwin yang diikuti 15 huruf: `ت ث ج د ذ ز س ش ص ض ط ظ ف ق ك`
- **Contoh:** `كُنتُمْ` → nun mati + `ت`

---

### **6. Ikhfa Syafawi (Mim Mati)**
- **Deteksi:** Cari mim mati (`مْ` atau `مۡ`) yang diikuti huruf `ب`
- **Contoh:** `هُمۡ بِالْأٓخِرَةِ`

---

### **7. Idgham Mimi (Mim Mati)**
- **Deteksi:** Cari mim mati (`مْ` atau `مۡ`) yang diikuti huruf `م`
- **Contoh:** `لَهُم مَّغْفِرَةٌ`
- **Catatan:** Jika ada tasydid, prioritas idgham mimi daripada izhar syafawi

---

### **8. Izhar Syafawi (Mim Mati)**
- **Deteksi:** Cari mim mati (`مْ` atau `مۡ`) yang diikuti **selain** `ب` dan `م`
- **Contoh:** `هُمۡ وَاللَّهُ`
- **Catatan:** Ini adalah default jika dua aturan di atas tidak terpenuhi

---

### **9. Qalqalah Sugra**
- **Deteksi:** Cari huruf qalqalah (`ق ط ب ج د`) yang bersukun (`ْ`) di tengah kata
- **Contoh:** `يَقْدِرُ` → qaf sukun
- **Catatan:** Tidak di akhir kata/ayat

---

### **10. Qalqalah Kubra**
- **Deteksi:** Cari huruf qalqalah (`ق ط ب ج د`) yang bersukun (`ْ`) di akhir kata/ayat
- **Contoh:** `وَقَدْ` → dal di akhir kata
- **Catatan:** Jika ada di akhir ayat, dianggap kubra

---

### **11. Ghunnah**
- **Deteksi:** Cari huruf `ن` atau `م` yang bertasydid (`ّ`)
- **Contoh:** `إِنَّ` → nun tasydid, `ثُمَّ` → mim tasydid

---

### **12. Alif Lam Syamsiah**
- **Deteksi:** Cari pola `ال` + salah satu 14 huruf syamsiah: `ت ث د ذ ر ز س ش ص ض ط ظ ل ن`
- **Contoh:** `ٱلَّذِينَ` → `ال` + `ذ`
- **Catatan:** Lam (`ل`) dilebur ke huruf syamsiah

---

### **13. Alif Lam Qamariah**
- **Deteksi:** Cari pola `ال` + salah satu 14 huruf qamariah: `ء ب غ ح ج ك و خ ف ع ق ي م ه`
- **Contoh:** `ٱلْمُؤْمِنِينَ` → `ال` + `م`
- **Catatan:** Lam (`ل`) dibaca jelas

---

### **14. Mad Asli (Thabi'i)**
- **Deteksi:** Cari salah satu pola:
  - `fathah + alif` (contoh: قَالَ)
  - `dammah + waw` (contoh: يَقُولُ)
  - `kasrah + ya` (contoh: فِي)
- **Catatan:** Dibaca 2 harakat

---

### **15. Mad Wajib Muttasil**
- **Deteksi:** Cari huruf mad (`ا و ي`) yang diikuti hamzah (`ء`) dalam satu kata
- **Contoh:** `جَاءَ` → alif + hamzah
- **Catatan:** Dibaca 4-5 harakat

---

### **16. Mad Jaiz Munfasil**
- **Deteksi:** Cari huruf mad (`ا و ي`) di akhir kata, yang diikuti hamzah (`ء`) di awal kata berikutnya
- **Contoh:** `بِمَا أُنزِلَ` → alif di akhir kata + hamzah di awal kata berikutnya
- **Catatan:** Dibaca 2-5 harakat

---

### **17. Mad Lazim Mutsaqqal**
- **Deteksi:** Cari huruf mad (`ا و ي`) yang diikuti huruf bertasydid (`ّ`)
- **Contoh:** `الضَّالِّينَ` → alif + lam bertasydid
- **Catatan:** Dibaca 6 harakat

---

### **18. Mad Lazim Mukhaffaf**
- **Deteksi:** Cari huruf mad (`ا و ي`) yang diikuti sukun (`ْ`), atau huruf muqatha'ah (`الم`, `كهيعص`)
- **Contoh:** `الم` → alif + lam + mim (huruf muqatha'ah)
- **Catatan:** Dibaca 6 harakat

---

### **19. Mad Aridh Lissukun**
- **Deteksi:** Cari huruf mad (`ا و ي`) di akhir kata, pada kata terakhir ayat (`is_last_word=True`)
- **Contoh:** `يَعْلَمُونَ` → waw mad di akhir kata
- **Catatan:** Dibaca 2-6 harakat, hanya saat waqaf

---

### **20. Mad Lin**
- **Deteksi:** Cari waw sukun (`وْ`) atau ya sukun (`يْ`) yang didahului fathah (`َ`)
- **Contoh:** `خَوْفٌ` → waw sukun didahului fathah
- **Catatan:** Dibaca 2-6 harakat

---

### **21. Mad Iwad**
- **Deteksi:** Cari tanwin fathah (`ً`) di akhir kata (pada kata terakhir ayat)
- **Contoh:** `عَلِيمًا` → tanwin fathah di akhir kata
- **Catatan:** Tanwin fathah berubah jadi alif, dibaca 2 harakat

---

### **22. Idgham Mutamatsilain**
- **Deteksi:** Cari dua huruf yang sama bertemu, huruf pertama mati (sukun)
- **Contoh:** `قَدْ دَخَلُواْ` → dal mati + dal
- **Catatan:** Huruf pertama dilebur ke huruf kedua

---

### **23. Idgham Mutajanisain**
- **Deteksi:** Cari pasangan huruf yang makhraj sama tapi sifat berbeda, huruf pertama mati
- **Pasangan:** `ت-د`, `د-ت`, `ت-ط`, `د-ط`, `ط-د`, `ث-ذ`, `ذ-ث`, `ب-م`, `ل-ر`
- **Contoh:** `قَدْ تَّبَيَّنَ` → dal mati + ta
- **Catatan:** Huruf pertama dilebur ke huruf kedua

---

### **24. Idgham Mutaqaribain**
- **Deteksi:** Cari pasangan huruf yang makhraj berdekatan, huruf pertama mati
- **Pasangan:** `ق-ك`, `ن-ل`, `ن-ر`
- **Contoh:** `أَلَمْ نَخْلُقْكُمْ` → qaf + kaf
- **Catatan:** Huruf pertama dilebur ke huruf kedua

---

## 🎯 **Alur Deteksi di Engine**

```
1. Input: Teks Arab Utsmani
2. Split menjadi kata-kata
3. Untuk setiap kata:
   a. Cek Nun Mati/Tanwin → klasifikasi ke 5 aturan (1-5)
   b. Cek Mim Mati → klasifikasi ke 3 aturan (6-8)
   c. Cek Qalqalah → klasifikasi ke 2 aturan (9-10)
   d. Cek Ghunnah → 1 aturan (11)
   e. Cek Alif Lam → klasifikasi ke 2 aturan (12-13)
   f. Cek Mad → klasifikasi ke 8 aturan (14-21)
   g. Cek Idgham → klasifikasi ke 3 aturan (22-24)
4. Resolve priority (jika ada overlap)
5. Filter berdasarkan level user (basic/intermediate/expert)
6. Return list rules
```

**Priority Rules (yang lebih prioritas menang):**
| Rule | Override |
|------|----------|
| Idgham Bighunnah | → Mutamatsilain, Mutaqaribain |
| Idgham Bilaghunnah | → Mutamatsilain, Mutaqaribain |
| Mad Wajib/Jaiz/Lazim | → Mad Asli |
| Mad Iwad | → Mad Aridh, Mad Asli |
| Qalqalah Kubra | → Qalqalah Sugra |

---

**Dokumen ini untuk validasi ke guru agama/ustadz.** 🚀