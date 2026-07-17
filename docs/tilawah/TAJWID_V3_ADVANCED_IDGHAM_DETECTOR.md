# Tajwid v3 — Advanced Idgham Detector

## Scope

Stage 5K mendeteksi tiga hubungan:

1. **Mutamathilain** — dua huruf identik; huruf pertama sakinah dan huruf kedua
   berharakat.
2. **Mutajanisain** — dua huruf semakhraj dengan sifat berbeda pada exact-pair
   table Hafs.
3. **Mutaqaribain** — dua huruf yang makhraj atau sifatnya berdekatan pada
   exact-pair table Hafs.

## Exact-pair table

### Mutajanisain

```text
تْ + د
دْ + ت
تْ + ط
طْ + ت
ثْ + ذ
ذْ + ظ
بْ + م
```

### Mutaqaribain

```text
لْ + ر
قْ + ك
```

Mutamathilain menggunakan kesamaan huruf secara langsung, dengan exclusion untuk
huruf madd dan keluarga yang sudah memiliki detector khusus.

## Span contract

```text
trigger span = huruf pertama yang sakinah
context span = trigger + separator + target
render span  = sama dengan context span
```

Contoh:

```text
قُلْ رَّبِّ
trigger = لْ
context = لْ رَّ
display = لْ رَّ
```

## Conflict dengan Qalqalah

Huruf `دْ`, `بْ`, atau `قْ` secara ortografis dapat memenuhi pola Qalqalah
Sughra. Ketika huruf tersebut dilebur ke huruf berikutnya, release qalqalah tidak
boleh dinilai sebagai target acoustic terpisah.

Conflict resolver menghapus annotation qalqalah hanya jika trigger span-nya
benar-benar tercakup oleh annotation Advanced Idgham. Qalqalah lain di ayat yang
sama tetap dipertahankan.

## Pengecualian huruf madd

Waw sakinah setelah dammah dan Ya sakinah setelah kasrah adalah carrier Mad.
Mereka tidak boleh dilebur oleh Mutamathilain generik.

```text
قُوْ وُعِدَ  → bukan Mutamathilain pada وْ + و
قِيْ يَقِينًا → bukan Mutamathilain pada يْ + ي
```

Waw atau Ya lin setelah fathah tidak masuk exclusion ini dan tetap dapat
dievaluasi menurut hubungan konsonan yang relevan.

## Deduplikasi keluarga khusus

```text
مْ + م → idgham_mimi
نْ + ن → idgham_bighunnah
```

Advanced Idgham tidak mengeluarkan `idgham_mutamathilain` pada dua locus itu.

## Idgham tidak lengkap

Pada `طْ + ت`, sifat itbaq/isti'la dari Tha tetap diperhitungkan. Annotation
menyimpan:

```json
{
  "assimilation_completeness": "incomplete",
  "retained_feature": "itbaq_istila"
}
```

## Qaf + Kaf

Pada locus `أَلَمْ نَخْلُقكُّم`, metadata acoustic menyimpan dua face:

```json
{
  "allowed_assimilation_faces": ["complete", "incomplete"],
  "preferred_face": "complete"
}
```

Label ini tetap provisional sampai review ahli dan kalibrasi audio. Engine tidak
memaksakan satu target acoustic sebagai satu-satunya bacaan yang diterima.

## Haa as-sakt

Boundary Haa as-sakt seperti `مَالِيَهْ هَلَكَ` belum diputuskan di Stage 5K.
Detector mengeluarkan warning:

```text
haa_sakt_idgham_deferred
```

Resolusi final dilakukan pada Stage 5L bersama Waqaf dan Saktah, agar pilihan
saktah atau idgham tidak dipisahkan dari boundary context.

## Beta policy

Annotation Stage 5K boleh masuk candidate seed dan ditampilkan ke frontend beta
sebagai `is_verified=false`. Expert correction tetap memiliki versi dan prioritas
lebih tinggi daripada hasil regenerasi engine.
