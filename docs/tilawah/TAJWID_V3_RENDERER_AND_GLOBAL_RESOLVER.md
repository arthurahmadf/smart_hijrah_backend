# Tajwid v3 — Global Resolver and Frontend Renderer

## Scope

Stage 5M converts semantic Tajwid annotations into a non-overlapping frontend
segment stream while preserving every underlying annotation for audit and later
expert review.

Pipeline:

```text
All text detectors
→ semantic conflict resolver
→ global annotation validation
→ mode-aware annotation set
→ atomic display partition
→ visual-priority resolver
→ exact frontend segments
```

## Two different kinds of conflict

### Semantic conflict

Two rules cannot both be true on the same trigger, for example:

- `ra_tafkhim` and `ra_tarqiq`;
- `qalqalah_sughra` and `qalqalah_kubra`;
- `alif_lam_qamariyyah` and `alif_lam_shamsiyyah`.

The global resolver selects one deterministic winner and emits a warning so the
conflict can be inspected in corpus reports.

### Visual overlap

Two rules can both be valid but cover the same grapheme, for example:

- Alif Lam Shamsiyyah and Ra Tafkhim;
- Hamzat Wasl and Alif Lam;
- Idgham and Ghunnah;
- Mad and a neighboring articulation rule.

Visual overlap is not deleted. The renderer stores all active rule codes and
selects one primary color using an explicit priority table.

## Frontend contract

Minimal output remains:

```json
{
  "rule_name": "mad",
  "color": "0xFF256E99",
  "rule_description": "...",
  "arabic": "مِينَ"
}
```

Every grapheme of the source ayah occurs exactly once across the returned
segments. Regular gaps, whitespace, Quranic marks, and punctuation are retained.

Extended internal output also includes:

```text
primary_rule_code
rule_codes
rule_titles
grapheme/codepoint span
confidence
reading_mode
is_verified
source
renderer_version
```

The minimal API can remain stable while backend/admin tools use extended fields.

## Beta verification policy

Engine-generated segments may be returned to the beta frontend with:

```text
is_verified = false
source = engine
```

Expert corrections later use a separate annotation-set version. Re-running the
engine must not overwrite a protected expert-verified version.

## Multi-mode analysis

An ayah can produce different expected laws depending on recitation mode.

Example at the end of Al-Fatihah 1:2:

```text
wasl      → mad_tabii on مِي
ayah_stop → mad_arid_lissukun on مِينَ
```

`analyze_tajwid_v3_modes()` preserves both sets and records which mode emitted
each rule. Stage 5N will choose the stored/published mode policy for frontend
endpoints.

## Renderer invariants

1. Segment text is never empty.
2. Segment spans are contiguous.
3. Concatenating `arabic` reproduces the source text byte-for-byte/codepoint-for-codepoint.
4. Every emitted rule has a display definition and Flutter ARGB color.
5. Overlapping semantic annotations are preserved as secondary rules.
6. Mutually exclusive rules may not remain unresolved after the global resolver.
7. `regular` is generated dynamically and is never stored as a Tajwid rule row.

## Full corpus audit

Stage 5M audits both `ayah_stop` and `wasl` modes, validates renderer
reconstruction, counts overlap signatures, and reports mode differences.
The command is read-only and does not seed annotations.
