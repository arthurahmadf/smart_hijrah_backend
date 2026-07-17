# Tajwid v3 Stage 5I — Alif Lam dan Lam Jalalah

## Cakupan

Detector ini menghasilkan exact-span annotation untuk:

- `alif_lam_qamariyyah`
- `alif_lam_shamsiyyah`
- `lam_jalalah_tafkhim`
- `lam_jalalah_tarqiq`

## Prinsip desain

1. Lam ta'rif dikenali dari token grapheme, bukan dari pencarian substring setelah klasifikasi.
2. Prefix melekat seperti `وَالْ`, `بِالْ`, `فَالْ`, serta kontraksi `لِلْ` tidak ikut diwarnai sebagai bagian rule.
3. Kata berhamzah asli seperti `أَلْهَاكُمُ` tidak dianggap definite article.
4. Lafz Allah dikecualikan dari Alif Lam Qamariyyah/Syamsiyyah dan ditangani detector Lam Jalalah.
5. Lam Jalalah menentukan tafkhim/tarqiq dari vokal terucap sebelum lafz Allah, termasuk carrier vokal panjang seperti `فِي`.
6. Ketika lafz Allah menjadi awal bacaan, default-nya tafkhim.
7. Jika vokal sebelumnya tidak dapat diselesaikan secara aman, detector mengeluarkan warning dan abstain.

## Span contract

### Lam ta'rif

Untuk `ٱلْقَمَرُ`:

- trigger: `ٱلْقَ`
- context: `ٱلْقَ`
- display: `ٱلْقَ`

Untuk `لِلْمُتَّقِينَ`, prefix `لِ` tidak diwarnai:

- trigger/context/display: `لْمُ`

### Lam Jalalah

Untuk `بِسْمِ ٱللَّهِ`:

- trigger: `لَّ`
- context: `ٱللَّ`
- display: `لَّ`
- rule: `lam_jalalah_tarqiq`

## Guardrail

- Qamariyyah tanpa sukun eksplisit: confidence 0.95 + warning.
- Syamsiyyah tanpa shadda eksplisit: confidence 0.95 + warning.
- Mad Farq dan interrogative hamza tidak dipaksa menjadi definite article.
- Candidate annotation tetap boleh tampil di frontend beta dengan `is_verified=false`.
