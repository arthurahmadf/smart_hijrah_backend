# Tajwid v3 — Database, Beta Publication, dan Expert Review

## Prinsip publikasi

Stage 5N memisahkan dua konsep:

1. **Published to beta** — annotation set aktif dan boleh dikirim ke frontend.
2. **Expert verified** — annotation atau satu set telah diperiksa ahli tajwid.

Candidate engine dapat berstatus `published` dan `is_active=true` walaupun seluruh
annotation masih `is_verified=false`. Ini disengaja agar beta dan review ahli
berjalan paralel.

## Proteksi hasil ahli

Set dianggap terlindungi bila:

- `verified_at` sudah terisi; atau
- minimal satu annotation memiliki `is_verified=true`.

Seed engine berikutnya tidak mengganti active set terlindungi. Candidate versi
baru tetap boleh dibuat sebagai set `validated` nonaktif untuk diperiksa.

## Mode database

- `ayah` menyimpan hasil `ayah_stop` dan menjadi sumber field `rules` frontend.
- `wasl` menyimpan analisis ayat dalam mode sambung.
- `waqf` tersedia untuk kebutuhan audit khusus.

## Endpoint

Serializer mengambil annotation set aktif mode `ayah` dari database, bukan
menjalankan engine saat request. Query list dan random memakai prefetch sehingga
tidak menimbulkan N+1 query.

Jika set belum tersedia, stale, atau gagal direkonstruksi, frontend menerima satu
segment `regular` yang berisi seluruh ayat. Endpoint tidak gagal hanya karena
annotation bermasalah.

## Workflow ahli

1. Buka **Tilawah Ayah Tajwid Annotation Sets** di Django Admin.
2. Filter `is_active=true`, `reading_mode=ayah`, dan status verifikasi.
3. Periksa inline annotation pada satu ayat.
4. Ubah rule bila salah, hapus false positive, atau beri catatan.
5. Jalankan action **Tandai seluruh anotasi sebagai terverifikasi ahli**.
6. `verified_at`, `reviewed_by`, dan `annotation.is_verified` akan diperbarui.

Hasil ahli tetap aktif di frontend dan terlindungi dari automatic reseed.
