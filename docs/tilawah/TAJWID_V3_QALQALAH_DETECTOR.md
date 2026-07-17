# Tajwid Engine v3 — Qalqalah Detector

## Scope

Detector menghasilkan tiga candidate annotation:

- `qalqalah_sughra`: salah satu huruf `ق ط ب ج د` memiliki sukun eksplisit dan tidak menjadi posisi waqaf aktual.
- `qalqalah_kubra`: huruf qalqalah non-mushaddad menjadi huruf terakhir yang dibaca ketika `reading_mode=waqf` atau `ayah_stop`.
- `qalqalah_akbar`: huruf qalqalah bertasydid menjadi huruf terakhir yang dibaca ketika waqaf.

## Kebijakan konservatif

- Huruf mushaddad di tengah bacaan tidak diberi warna qalqalah sampai kebijakan fonologisnya diverifikasi ahli.
- Pada satu locus waqaf, `kubra` atau `akbar` menggantikan `sughra`; tidak dibuat anotasi ganda.
- `qalqalah_akbar` mempunyai confidence 0.95 karena label tiga tingkat masih provisional untuk review ahli, walaupun posisi huruf dan shadda terdeteksi deterministik.
- Detector tidak mengukur kualitas pantulan suara. `release_strength` adalah expected feature untuk acoustic evaluator berikutnya.

## Reading mode

- `wasl`: hanya qalqalah sughra dari sukun eksplisit.
- `waqf`: akhir input dianggap tempat berhenti.
- `ayah_stop`: hubungan di dalam ayat dibaca terus dan akhir input dianggap tempat berhenti.

## False-positive guardrails

- huruf harus termasuk `ق ط ب ج د`;
- sughra membutuhkan sukun eksplisit;
- kubra/akbar hanya boleh muncul pada huruf terakhir input;
- shadda + sukun eksplisit bersamaan dianggap structural error;
- huruf bergerak di tengah bacaan tidak menghasilkan qalqalah.
