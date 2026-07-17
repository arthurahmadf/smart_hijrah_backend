# Tajwid Engine v3 — Advanced Mad Resolver (Stage 5H)

## Scope

Stage 5H menambahkan candidate annotation untuk:

- Mad Tamkin
- Mad Silah Qasirah
- Mad Silah Tawilah
- Mad Lazim Harfi Muthaqqal
- Mad Lazim Harfi Mukhaffaf
- Mad Harfi Tabi'i
- Mad 'Ayn Muqatta'ah
- Mad Farq

Engine version: `3.0.0-alpha.5`.

## Design principles

1. Detector tidak menggunakan output engine legacy.
2. Exact grapheme span dibuat saat rule terdeteksi.
3. Mad Farq hanya aktif pada registry enam lokasi Hafs yang memiliki `verse_key`.
4. Huruf muqatta'ah memakai registry lokasi pembuka surah dan klasifikasi per huruf.
5. Mad Silah masih candidate morphology-sensitive; confidence di bawah 1.0 dan evidence menyimpan resolver yang digunakan.
6. Konflik Mad advanced vs Mad core diselesaikan secara deterministik tanpa menghapus rule lain yang memang boleh coexist.

## Silah limitations

Orthography saja tidak cukup untuk membedakan seluruh ha dhamir dari ha asli. Resolver Stage 5H memakai guardrail konservatif:

- ha harus final pada kata;
- hanya dammah/kasrah;
- didahului huruf berharakat;
- memiliki target kata berikutnya;
- lafz Allah dan sejumlah lexical/root-final ha dikecualikan;
- `يَرْضَهُ` dikecualikan sebagai lexical Hafs exception;
- hamzat wasl sesudah ha ditunda ke pronunciation resolver.

Sebelum expert verification, annotation Silah tetap boleh tampil pada beta dengan `is_verified=false`.

## Muqatta'ah

Registry mendukung seluruh lokasi pembuka surah Hafs, termasuk `42:2` untuk `عسق`. Klasifikasi yang dipakai:

- `حي طهر`: Mad Harfi Tabi'i;
- `عين`: Mad 'Ayn, 4 atau 6 harakat sesuai profil;
- kelompok lazim: enam harakat;
- `لام` sebelum `ميم`, dan `سين` sebelum `ميم`, diklasifikasikan sebagai Muthaqqal;
- bentuk lazim lainnya sebagai Mukhaffaf.

Taxonomy dan pilihan profil tetap disimpan sebagai candidate sampai review ahli.

## Mad Farq

Registry Hafs dibatasi pada:

- 6:143
- 6:144
- 10:51
- 10:59
- 10:91
- 27:59

Detector tidak menebak Mad Farq hanya dari bentuk ortografis tanpa `verse_key`.

## Conflict resolution

Advanced Mad dapat menggantikan Mad core jika trigger advanced mencakup trigger core pada locus yang sama. Contoh:

- Mad Farq menggantikan Mad Lazim Kalimi Mukhaffaf pada lokasi registry;
- Mad Tamkin menggantikan Mad Tabi'i pada nucleus ya yang sama.

Mad yang memiliki locus berbeda tetap coexist.
