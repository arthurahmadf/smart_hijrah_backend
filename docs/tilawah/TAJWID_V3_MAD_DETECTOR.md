# Tajwid Engine v3 — Mad Detector (Stage 5G)

## Scope

Stage 5G implements exact-span text detection for these nine rules:

- `mad_tabii`
- `mad_badl`
- `mad_iwad`
- `mad_wajib_muttasil`
- `mad_jaiz_munfasil`
- `mad_lazim_kalimi_muthaqqal`
- `mad_lazim_kalimi_mukhaffaf`
- `mad_arid_lissukun`
- `mad_lin`

The detector reads the canonical grapheme stream directly and does not consume
legacy Tajwid Engine output.

## Span contract

- `trigger_span`: the recited long-vowel unit, normally onset plus carrier.
- `context_span`: trigger plus the cause that changes the Mad category.
- `display_span`: the beta frontend highlight range.

Examples:

- `قَالَ` → trigger/display `قَا`
- `جَاءَ` → trigger `جَا`, context/display `جَاءَ`
- `فِي أَنْفُسِكُمْ` → trigger `فِي`, context/display `فِي أَ`
- `الْعَالَمِينَ` at ayah stop → trigger `مِي`, context/display `مِينَ`

## Priority

A single Mad nucleus emits the strongest applicable category:

1. actual-stop `mad_arid_lissukun`
2. `mad_wajib_muttasil`
3. `mad_lazim_kalimi_muthaqqal`
4. `mad_lazim_kalimi_mukhaffaf`
5. `mad_jaiz_munfasil`
6. `mad_badl`
7. `mad_tabii`

`mad_iwad` and `mad_lin` are stop-context rules and are detected separately.

## Uthmani handling

The detector supports:

- explicit and implicit-sukun Waw/Ya Mad carriers;
- dagger alif attached to a consonant (`مَٰ`);
- dagger alif encoded on a QPC tatweel extender (`مَـٰ`);
- silent support alif after plural Waw (`قَالُوا أَ...`);
- alif madda (`آ`) as a provisional Badl orthographic form.

## Conservative boundaries

The following remain deferred to later stages because they require lexical,
morphological, profile, or expert-assisted resolution:

- Mad Tamkin;
- Mad Silah Qasirah/Tawilah;
- Mad Lazim Harfi;
- Mad Harfi Tabi'i;
- Mad 'Ayn Muqatta'ah;
- Mad Farq.

An unresolved maddah sign produces a warning, not a fabricated rule.

## Verification policy

All generated annotations are eligible for beta frontend rendering when their
structural contract is valid. Until expert review, they remain marked as engine
generated and `is_verified=false` when persisted.
