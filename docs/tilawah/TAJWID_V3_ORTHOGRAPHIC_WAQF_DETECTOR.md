# Tajwid Engine v3 — Stage 5L Orthographic and Waqf Layer

Engine version: `3.0.0-alpha.9`

## Scope

Stage 5L completes the 44-rule provisional text taxonomy with:

- `hamzat_wasl`
- `silent_letter`
- `saktah_wajibah`
- `saktah_jaizah`

It also extracts Unicode waqf signs into typed metadata. Generic waqf signs are not
invented as Tajwid rule codes because they describe stopping guidance rather than a
single pronunciation law.

## Hamzat Wasl

The detector recognizes the explicit QPC/Uthmani character `ٱ`.

- At the beginning of the input it is marked `pronounced_at_ibtida`.
- After a preceding pronounced letter it is marked `dropped_in_wasl`.
- The starting vowel is resolved conservatively:
  - definite article: fatha;
  - registered سماعية nouns: kasra;
  - verbal form: damma when the third written consonant is explicitly dammed,
    otherwise kasra when the evidence is explicit;
  - unresolved morphology remains `null` and is not guessed.

This rule is render-only and must not directly reduce an acoustic score.

## Silent letters

The detector only trusts explicit QPC/Uthmani orthographic marks:

- `U+06DF ARABIC SMALL HIGH ROUNDED ZERO`: ignored in both connected and
  stopped reading;
- `U+06E0 ARABIC SMALL HIGH UPRIGHT RECTANGULAR ZERO`: ignored in wasl but
  restored when actually stopping on the marked letter.

Plain unmarked letters are not labelled silent by shape alone.

## Saktah

The recitation profile remains Hafs from Asim through al-Shatibiyyah.

Mandatory registry:

- `18:1 → 18:2`: `عِوَجَا / قَيِّمًا`
- `36:52`: `مَرْقَدِنَا / هَذَا`
- `75:27`: `مَنْ / رَاقٍ`
- `83:14`: `بَلْ / رَانَ`

Optional registry:

- `69:28 → 69:29`: `مَالِيَهْ / هَلَكَ`
- `8:75 → 9:1`: `عَلِيمٌ / بَرَاءَةٌ`

A saktah annotation can be generated from the exact profile registry even when a
font/text variant omits `U+06DC`. Missing markers reduce confidence and remain
reviewable.

When a saktah is active, cross-boundary Nun/Tanwin, Mim Sakinah, or Advanced
Idgham annotations at the same trigger are suppressed because the letters do not
meet acoustically across the breathless pause.

## Waqf metadata

`waqf.py` maps these Unicode signs:

- `U+06D6`: continue preferred;
- `U+06D7`: stop preferred;
- `U+06D8`: mandatory stop;
- `U+06D9`: do not stop;
- `U+06DA`: permissible stop;
- `U+06DB`: paired stop;
- `U+06DC`: saktah.

The result is exposed through `TajwidEngineV3Result.waqf_hints` and `to_dict()`.
These hints are metadata for Stage 5M rendering, not new database rule rows.

## External reference roles

- Quran Foundation/Quran.com documents `text_qpc_hafs` and Uthmani Tajweed text
  as Unicode Quran resources suitable for rendering and cross-reference.
- QUL publishes the QPC Hafs Unicode script derived from the King Fahd Complex.
- The Hafs saktah profile and breathless-pause behavior must remain subject to
  expert talaqqi review before verified status.

## Beta policy

All Stage 5L annotations may be published to the beta frontend with:

- `is_verified = false`
- exact `engine_version`
- candidate provenance
- expert corrections protected from regeneration

Structural success does not equal expert verification.
