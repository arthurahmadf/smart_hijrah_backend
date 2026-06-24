## 📋 **Dokumentasi Lengkap Smart Hijrah - Status Pengembangan & Roadmap**

---

### 1. Ringkasan Eksekutif

Smart Hijrah adalah aplikasi mobile berbasis Flutter dengan backend Django yang membantu umat Muslim mempelajari Islam melalui berbagai fitur: social feed, spiritual tracker, edukasi tajwid, gamifikasi, dan AI-assisted learning.

**Status:** MVP Production Ready (75% fitur selesai)

---

### 2. Fitur yang Sudah Selesai (✅)

#### 2.1. User & Authentication
| Fitur | Status | Keterangan |
|-------|--------|------------|
| Register user | ✅ | Dengan verifikasi email via Brevo |
| Login JWT | ✅ | Username/email fleksibel |
| Login Google OAuth | ✅ | Web application + token verification |
| Profile management | ✅ | Get, update, change password, profile picture |
| Email verification | ✅ | HTML email dengan deep link |
| Resend verification | ✅ | Via email |

#### 2.2. Today (Social Feed)
| Fitur | Status | Keterangan |
|-------|--------|------------|
| Feed (Global/Local/Following) | ✅ | 3 endpoint berbeda |
| Create feed | ✅ | Max 5 gambar |
| Like/Unlike feed | ✅ | - |
| Comment feed | ✅ | Add, delete, get |
| Follow/Unfollow | ✅ | + get followers/following |
| Stories | ✅ | Upload image/video, 3 endpoint |

#### 2.3. Lifestyle
| Fitur | Status | Keterangan |
|-------|--------|------------|
| Fest (Event) | ✅ | Headlines, recommendations, all fest |
| Nearby Masjids | ✅ | Geoapify API + review/rating |
| Nearby Kliniks | ✅ | Geoapify API + review/rating |
| Umrah & Haji | ❌ | Belum dikerjakan |
| Scholarship | ❌ | Belum dikerjakan |
| E-Course | ❌ | Belum dikerjakan |

#### 2.4. Belajar Ngaji
| Fitur | Status | Keterangan |
|-------|--------|------------|
| Kelas Tahfidz | ✅ | List, search, detail, enroll |
| Pelajaran (Learning Path) | ✅ | Steps, progress, materi (arabic/latin/audio) |
| Enrollment dengan data lengkap | ✅ | Nama, usia, orang tua, dll |

#### 2.5. Explore
| Fitur | Status | Keterangan |
|-------|--------|------------|
| Kisah Nabi | ✅ | List, popular, detail, read count |
| Hijrah Kids | ❌ | Belum dikerjakan |
| Hijrah Podcast | ❌ | Belum dikerjakan |

#### 2.6. Spiritual Tracker (Monitor Shalat)
| Fitur | Status | Keterangan |
|-------|--------|------------|
| Monitor shalat | ✅ | Status: null/false/true |
| Mark prayer completed | ✅ | Tambah poin gamifikasi |
| Prayer history | ✅ | Date range |
| Prayer statistics | ✅ | Current month |
| Notification preferences | ✅ | Per shalat |

#### 2.7. Gamifikasi
| Fitur | Status | Keterangan |
|-------|--------|------------|
| Leaderboard | ✅ | Info + rank + top 50 |
| Amalan check-in | ✅ | Idempotent (true/false) |
| Jejak Hijrah | ✅ | Streak, monitor, level info |
| Level system | ✅ | Starter → Diamond (6 level) |
| Poin per amalan | ✅ | 7 amalan + shalat wajib |
| Streak system | ✅ | Minimal 3 hari baru tampil |

#### 2.8. Tilawah Assistant (AI)
| Fitur | Status | Keterangan |
|-------|--------|------------|
| Get random ayah by level | ✅ | Basic/Intermediate/Expert |
| Tarteel Whisper STT | ✅ | Model di-local, transkripsi audio |
| Word matching | ✅ | LCS algorithm + phonetic fallback |
| Tajwid Engine | ✅ | 20+ hukum tajwid |
| Level filter | ✅ | Basic/Intermediate/Expert |
| Feedback builder | ✅ | Per kata, correction + caption |
| Scoring | ✅ | Word accuracy + Tajwid score |
| Database Quran | ✅ | Utsmani + transliterasi + terjemahan |
| Endpoint submit tilawah | ✅ | Complete response |

#### 2.9. Smart AI (Chatbot)
| Fitur | Status | Keterangan |
|-------|--------|------------|
| Chat dengan Gemini | ✅ | Model: gemini-2.5-flash-lite |
| Multi-turn conversation | ✅ | History dari database |
| Get conversations | ✅ | Daftar percakapan user |
| Get conversation detail | ✅ | History messages |
| Delete conversation | ✅ | - |

#### 2.10. Faraid (Waris Islam)
| Fitur | Status | Keterangan |
|-------|--------|------------|
| Perhitungan waris | ✅ | Rule-based engine |
| Riwayat perhitungan | ✅ | - |
| Detail perhitungan | ✅ | - |

---

### 3. Fitur yang Belum Selesai (❌)

| No | Fitur | Prioritas | Keterangan |
|----|-------|-----------|------------|
| 1 | Hijrah Kids | 🟡 Medium | Series, channel, kategori |
| 2 | Hijrah Podcast | 🟡 Medium | Podcast, episodes, popular |
| 3 | Umrah & Haji | 🟢 Low | Packages, jamaah tracking |
| 4 | Scholarship | 🟢 Low | Beasiswa, institution |
| 5 | E-Course | 🟢 Low | Enrollment, progress |
| 6 | Notification push | 🟡 Medium | Firebase FCM |

---

### 4. Segmen Khusus: Tilawah Assistant

#### 4.1. Arsitektur Sekarang

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Flutter App   │────▶│   Django API    │────▶│ Tarteel Whisper │
│  (Rekam Audio)  │     │  /tilawah/...   │     │   (STT Model)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │                         │
                              ▼                         │
                        ┌─────────────────┐             │
                        │  Word Matcher   │◀────────────┘
                        │  (LCS + Fallback)│
                        └─────────────────┘
                              │
                              ▼
                        ┌─────────────────┐
                        │  Tajwid Engine  │
                        │  (20+ hukum)    │
                        └─────────────────┘
                              │
                              ▼
                        ┌─────────────────┐
                        │ Feedback Builder│
                        │  (Per kata)     │
                        └─────────────────┘
```

#### 4.2. Detail Komponen

| Komponen | Status | File | Keterangan |
|----------|--------|------|------------|
| **Whisper Engine** | ✅ Production | `whisper_engine.py` | Tarteel Whisper Base AR Quran, model di-local |
| **Word Matcher** | ✅ Production | `word_matcher.py` | LCS + phonetic fallback (Qaf/Kaf + dammah) |
| **Tajwid Engine** | ✅ Production | `tajwid_engine.py` | 20+ hukum, level filter, priority resolution |
| **Feedback Builder** | ✅ Production | `feedback_builder.py` | Per kata, correction + caption + skor |
| **Quran Database** | ✅ Production | `TilawahAyahPool` | Utsmani + transliterasi + terjemahan |
| **Endpoint** | ✅ Production | `tilawah_views.py` | `/tilawah/ayah/random/`, `/tilawah/submit/` |

#### 4.3. Hukum Tajwid yang Didukung

| Level | Jumlah Hukum | Daftar |
|-------|-------------|--------|
| **Basic** | 8 | Izhar Halqi, Idgham Bighunnah, Idgham Bilaghunnah, Iqlab, Ikhfa Haqiqi, Mim Mati (3), Qalqalah (2), Ghunnah, Alif Lam (2), Mad Asli |
| **Intermediate** | 8 | Mad Wajib Muttasil, Mad Jaiz Munfasil, Mad Lazim Mutsaqqal, Mad Lazim Mukhaffaf, Mad Aridh Lissukun, Mad Lin, Mad Iwad, Idgham Mutamatsilain |
| **Expert** | 4 | Mad Silah (2), Tafkhim/Tarqiq Ra, Lam Jalalah |

#### 4.4. Keterbatasan Saat Ini

| No | Batasan | Dampak | Solusi |
|----|---------|--------|--------|
| 1 | **Feedback per kata, bukan per huruf** | User tidak tahu huruf mana yang salah | Butuh mapping posisi huruf di UI |
| 2 | **Tidak bisa menilai makhraj** | Feedback hanya berdasarkan teks | Butuh analisis audio (librosa) |
| 3 | **Tidak bisa mengukur panjang mad** | Feedback mad hanya ada/tidak | Butuh analisis durasi audio |
| 4 | **Tidak bisa menilai kualitas ghunnah** | Feedback ghunnah hanya ada/tidak | Butuh analisis sinyal audio |
| 5 | **Fallback Qaf/Kaf terbatas** | Hanya untuk vokal dammah | Bisa ditambah untuk kasrah jika diperlukan |
| 6 | **Tidak ada audio contoh per huruf** | User tidak bisa dengar contoh benar | Butuh database audio atau TTS |

#### 4.5. Roadmap Pengembangan Tilawah

**Fase 1 (Selesai ✅)**
- Tajwid Engine dengan 20+ hukum
- Integrasi Tarteel Whisper
- Word matching dengan LCS
- Feedback per kata + skor
- Level filter (Basic/Intermediate/Expert)

**Fase 2 (Next - 1-2 bulan)**
| Tugas | Estimasi | Keterangan |
|-------|----------|------------|
| Feedback per huruf (color coding) | 1 minggu | Mapping posisi huruf ke feedback |
| Audio contoh per hukum (TTS) | 1 minggu | Pakai Google TTS atau Microsoft Azure TTS |
| Penambahan Mad Silah | 3 hari | Sudah ada di engine, tinggal testing |
| Penambahan Tafkhim/Tarqiq Ra | 3 hari | Sudah ada di engine, tinggal testing |
| Database audio per kata (premium) | 2 minggu | Kumpulkan audio dari qari terkenal (opsional) |
| Endpoint streaming | 1 minggu | Feedback real-time (per kata) |

**Fase 3 (3-6 bulan)**
| Tugas | Estimasi | Keterangan |
|-------|----------|------------|
| Penilaian makhraj (librosa) | 1-2 bulan | Analisis frekuensi audio untuk posisi lidah |
| Penilaian panjang mad (librosa) | 2 minggu | Analisis durasi audio |
| Gamifikasi tilawah | 1 bulan | Streak, poin, lencana khusus tilawah |
| Database audio per huruf (expert) | 1 bulan | Kumpulkan audio contoh per huruf dari qari |
| Offline mode (on-device Whisper) | 2 bulan | Pakai TFLite atau ONNX untuk Flutter |

**Fase 4 (6+ bulan - Research)**
| Tugas | Estimasi | Keterangan |
|-------|----------|------------|
| Real-time feedback kata per kata | 2 bulan | Streaming audio, feedback langsung |
| AI makhraj scoring | 6+ bulan | Train model sendiri untuk deteksi makhraj |
| Multi-qira'at support | 6+ bulan | Support qira'at lain (Hafs, Warsh, dll) |

---

### 5. Arsitektur Backend (Django)

```
main/
├── models.py + models_*.py (10+ model files)
├── serializers/ (10+ serializer files)
├── endpoint/
│   ├── social/ (feed, story, comment, follow)
│   ├── lifestyle/ (fest)
│   ├── ngaji/ (kelas, pelajaran)
│   ├── ai/ (chat_views)
│   ├── masjid_views.py
│   ├── klinik_views.py
│   ├── spiritual_views.py
│   ├── gamification_views.py
│   ├── tilawah_views.py
│   └── faraid_views.py
├── utils/
│   ├── gamification_constants.py
│   ├── gamification_helpers.py
│   └── tilawah/
│       ├── tajwid_engine.py
│       ├── word_matcher.py
│       ├── whisper_engine.py
│       └── feedback_builder.py
├── google_auth_views.py
├── email_utils.py
├── gemini_client.py
└── urls.py
```

---

### 6. Database Overview

| Model | Jumlah | Keterangan |
|-------|--------|------------|
| User | - | Custom user model |
| Feed | - | Social feed |
| Story | - | Stories |
| Fest | - | Event/ festival |
| MasjidReview | - | Review masjid |
| KlinikReview | - | Review klinik |
| KelasTahfidz | - | Kelas ngaji |
| TilawahAyahPool | 6.236 | Teks Quran + transliterasi + terjemahan |
| ChatConversation | - | History chat AI |
| ChatMessage | - | Messages chat AI |
| UserLevel | - | Gamifikasi level |
| AmalanCheckin | - | Check-in harian |
| InheritanceSession | - | Perhitungan waris |

---

### 7. Tech Stack

| Layer | Teknologi |
|-------|-----------|
| Backend | Django 5.0 + DRF |
| Database | PostgreSQL |
| Authentication | JWT (SimpleJWT) + Google OAuth2 |
| AI Model | Tarteel Whisper (STT), Google Gemini (Chat) |
| Maps | Geoapify API |
| Email | Brevo SMTP |
| Deployment | (Belum ditentukan) |

---

### 8. Metrik & Target

| Metrik | Target Saat Ini | Target 3 Bulan |
|--------|-----------------|----------------|
| Akurasi Tajwid Engine | 90%+ | 95%+ |
| Waktu Response Tilawah | 2-4 detik | < 2 detik |
| User Daily Active | - | 1.000+ |
| Fitur Selesai | 75% | 90% |

---

**Dokumen ini untuk meeting internal tim Smart Hijrah.** 🚀