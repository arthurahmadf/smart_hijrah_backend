# Tajwid v3 — Ra Tafkhim, Tarqiq, dan Dua Wajah (Stage 5J)

## Tujuan

Stage 5J menambahkan detector berbasis grapheme untuk hukum huruf **Ra (ر)** pada profil:

- Qira'ah: `Asim`
- Riwayah: `Hafs`
- Tariq: `al-Shatibiyyah`
- Mode default aplikasi: wasal di dalam ayat dan waqaf di akhir ayat.

Detector menghasilkan exact `trigger_span`, `context_span`, dan `display_span`. Ia tidak menggunakan output Tajwid Engine legacy.

## Rule code

- `ra_tafkhim`
- `ra_tarqiq`
- `ra_both_permitted`

## Decision table yang diimplementasikan

### Tafkhim

- Ra berfathah atau berdammah, termasuk tanwin terkait.
- Ra sakinah didahului fathah atau dammah.
- Ra sakinah didahului kasrah sementara dari hamzat wasl.
- Ra sakinah didahului kasrah asli dan diikuti huruf isti'la dalam kata yang sama, kecuali lokasi profil yang mengizinkan dua wajah.
- Ketika waqaf, Ra mengikuti vokal yang mendahului langsung atau vokal sebelum konsonan sakinah.

### Tarqiq

- Ra berkasrah atau kasratan.
- Ra sakinah didahului kasrah asli dalam kata yang sama dan tidak diikuti huruf isti'la pemicu tafkhim.
- Ketika waqaf, Ra didahului ya sakinah/ya maddiyyah.
- Ketika waqaf, Ra didahului konsonan sakinah yang sebelumnya berkasrah.

### Dua wajah

Registry profil konservatif:

- `فِرْقٍ` pada `26:63`: tafkhim atau tarqiq ketika wasal; ketika berhenti pada kata, tafkhim.
- `مِصْر` pada `12:21`, `12:99`, dan `43:51`: dua wajah ketika waqaf pada kata.
- `الْقِطْر` pada `34:12`: dua wajah ketika waqaf pada kata.

Registry menggunakan `verse_key` agar bentuk ejaan yang sama di lokasi lain tidak otomatis memperoleh pengecualian.

## Kebijakan beta

Semua anotasi Stage 5J masih candidate:

- boleh ditampilkan ke frontend beta;
- `is_verified=false`;
- `engine_version=3.0.0-alpha.7`;
- koreksi ahli harus disimpan sebagai revisi yang terlindungi.

## Guardrail

- Detector abstain dengan warning jika konteks Ra tidak dapat diputuskan secara aman.
- Rule dua wajah tidak ditebak hanya dari bentuk kata; harus cocok dengan registry profil.
- Waqaf hanya diterapkan pada locus berhenti aktual, bukan pada semua Ra dalam ayat.
- Trigger/display hanya mewarnai grapheme Ra; context menyimpan bukti huruf/vokal terkait.
- Acoustic evaluation belum aktif; rule ini hanya expected-text annotation.

## Audit yang perlu diperhatikan

Warning berikut tidak dianggap structural error, tetapi distribusinya perlu ditinjau:

- `ra_without_resolvable_vowel_or_sukun`
- `ra_sakin_context_unresolved`
- `ra_waqf_context_unresolved`
- `ra_sakin_without_same_word_predecessor`

Jika warning sangat banyak, kirim report corpus sebelum candidate seed.
