# Smart Hijrah — AI Tilawah Roadmap

## Stage 5 — Expected Tajwid Text Engine

- 5A: formal specification and profile
- 5B: goldset schema and validation gates
- 5C: Unicode grapheme parser and token stream
- 5D: Nun Sakinah and Tanwin
- 5E: Mim Sakinah and Ghunnah
- 5F: Qalqalah
- 5G: Core Mad
- 5H: Advanced Mad
- 5I: Alif Lam and Lam Jalalah
- 5J: Ra Tafkhim/Tarqiq and permitted variants
- 5K: Mutamathilain, Mutajanisain, Mutaqaribain
- 5L: Hamzat Wasl, silent letters, waqf and saktah — completed
- 5M: global conflict resolver, frontend renderer, full corpus audit — completed
- 5N: candidate seed, beta publication, expert review workflow, ayah level recalibration — completed

## Stage 6 — Audio Quality Gate

- decode and format validation
- sample-rate normalization
- clipping/dropout/SNR metrics
- VAD and silence trimming
- invalid-recording abstention
- raw and enhanced dual audio paths

## Stage 7 — Recitation Alignment

- Quran-aware ASR confidence
- repetition-aware dynamic alignment
- self-correction/restart handling
- word and phoneme timestamps
- background speech and multi-speaker suspicion
- playback/reference-audio detection

## Stage 8 — Acoustic Tajwid Evaluation

- Mad duration evaluator
- Ghunnah duration/nasalization evaluator
- Qalqalah release evaluator
- pause/waqf/saktah evaluator
- confidence-weighted scoring and abstention

## Stage 9 — Makhraj and Phoneme Models

- phoneme-level forced alignment
- confusable-letter classifiers, including `ع/ا`, `ح/ه`, `ص/س`, `ض/ظ`, `ق/ك`
- age, gender, pitch and device calibration
- false-accusation controls

## Stage 10 — Scoring and Beta Calibration

- rule-specific precision/recall
- confidence calibration
- score normalization across ayah difficulty
- teacher/user beta review
- observability and error replay

## Stage 11 — Expert Review and Continuous Improvement

- Django Admin review queue
- annotation versioning
- verified corrections protected from regeneration
- disagreement analysis
- goldset expansion and active learning

## Stage 12 — Production Hardening

- async inference architecture
- CPU/GPU capacity planning
- cache and model lifecycle
- security/privacy and audio retention
- benchmark, load test, rollback and deployment gates

The plan currently ends at Stage 12. Stages 8–11 may run in parallel after Stage 5N and Stage 6 are stable.
