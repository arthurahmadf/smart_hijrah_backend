from __future__ import annotations

from types import MappingProxyType
from typing import Any, Mapping, Optional, Tuple

from .specification import (
    AcousticAssessment,
    AppliesWhen,
    DetectionMaturity,
    DisplayGroup,
    DisplaySpanPolicy,
    RuleFamily,
    TajwidRuleSpec,
    VerificationState,
    validate_rule_specs,
)


COMMON_SOURCES = (
    "QUL_QPC_HAFS_TAJWEED",
    "QURAN_FOUNDATION_TAJWEED_V4",
    "EXPERT_TALAQQI_REVIEW",
)

REFERENCE_ASSISTED_SOURCES = (
    "QUL_QPC_HAFS_TAJWEED",
    "QURAN_FOUNDATION_TAJWEED_V4",
    "QURAN_TAJWEED_JSON_LEGACY",
    "EXPERT_TALAQQI_REVIEW",
)

PROFILE_SOURCES = (
    "HAFS_SHATIBIYYAH_PROFILE",
    "EXPERT_TALAQQI_REVIEW",
)


def _rule(
    *,
    code: str,
    name: str,
    family: RuleFamily,
    display_group: DisplayGroup,
    description: str,
    applies_when: AppliesWhen,
    display_span_policy: DisplaySpanPolicy,
    detection_maturity: DetectionMaturity,
    acoustic_assessment: AcousticAssessment,
    trigger_spec: str,
    context_spec: str,
    exclusions: Tuple[str, ...] = (),
    expected_features: Optional[Mapping[str, Any]] = None,
    requires_profile: bool = False,
    verification_state: VerificationState = VerificationState.PROVISIONAL,
    source_ids: Tuple[str, ...] = COMMON_SOURCES,
    notes: str = "",
) -> TajwidRuleSpec:
    return TajwidRuleSpec(
        code=code,
        name=name,
        family=family,
        display_group=display_group,
        description=description,
        applies_when=applies_when,
        display_span_policy=display_span_policy,
        detection_maturity=detection_maturity,
        acoustic_assessment=acoustic_assessment,
        trigger_spec=trigger_spec,
        context_spec=context_spec,
        exclusions=exclusions,
        expected_features=expected_features or {},
        requires_profile=requires_profile,
        verification_state=verification_state,
        source_ids=source_ids,
        notes=notes,
    )


_RULES = (
    # ================================================================
    # Nun sakinah dan tanwin
    # ================================================================
    _rule(
        code="izhar_halqi",
        name="Izhar Halqi",
        family=RuleFamily.NUN_TANWIN,
        display_group=DisplayGroup.NUN_TANWIN,
        description="Nun sakinah atau tanwin bertemu huruf halqi dan dibaca jelas.",
        applies_when=AppliesWhen.CONTEXTUAL,
        display_span_policy=DisplaySpanPolicy.TRIGGER_AND_TARGET,
        detection_maturity=DetectionMaturity.CORE_DETERMINISTIC,
        acoustic_assessment=AcousticAssessment.ARTICULATION_MODEL,
        trigger_spec="Nun ber-sukun asli atau salah satu tanda tanwin.",
        context_spec="Huruf terucap berikutnya salah satu: ء ه ع ح غ خ.",
        exclusions=(
            "Tanda waqaf dan ornamen bukan huruf terucap.",
            "Jika berhenti pada trigger di akhir kata, rule lintas kata tidak berlaku.",
        ),
        expected_features={"clarity": True, "assimilation": False},
    ),
    _rule(
        code="izhar_mutlaq",
        name="Izhar Mutlaq",
        family=RuleFamily.NUN_TANWIN,
        display_group=DisplayGroup.NUN_TANWIN,
        description=(
            "Nun sakinah bertemu ya atau waw dalam kata yang sama dan tetap dibaca jelas."
        ),
        applies_when=AppliesWhen.BOTH,
        display_span_policy=DisplaySpanPolicy.TRIGGER_AND_TARGET,
        detection_maturity=DetectionMaturity.DETERMINISTIC_WITH_EXCEPTIONS,
        acoustic_assessment=AcousticAssessment.ARTICULATION_MODEL,
        trigger_spec="Nun sakinah di dalam kata.",
        context_spec=(
            "Huruf berikutnya ي atau و dalam kata yang sama; detector memakai "
            "lexicon Hafs yang telah diverifikasi, bukan aturan generik semata."
        ),
        exclusions=(
            "Jangan mengubah menjadi idgham bighunnah.",
            "Lexicon awal mencakup bentuk dari الدنيا، بنيان، صنوان، قنوان.",
        ),
        expected_features={"clarity": True, "assimilation": False},
        source_ids=REFERENCE_ASSISTED_SOURCES,
    ),
    _rule(
        code="idgham_bighunnah",
        name="Idgham Bighunnah",
        family=RuleFamily.NUN_TANWIN,
        display_group=DisplayGroup.IDGHAM,
        description=(
            "Nun sakinah atau tanwin dilebur ke huruf berikutnya dengan ghunnah."
        ),
        applies_when=AppliesWhen.WASL,
        display_span_policy=DisplaySpanPolicy.TRIGGER_AND_TARGET,
        detection_maturity=DetectionMaturity.DETERMINISTIC_WITH_EXCEPTIONS,
        acoustic_assessment=AcousticAssessment.ASSIMILATION_MODEL,
        trigger_spec="Nun sakinah atau tanwin pada akhir unit kata.",
        context_spec="Huruf terucap berikutnya salah satu ي ن م و pada kata berikutnya.",
        exclusions=(
            "Izhar mutlaq dalam kata yang sama.",
            "Kasus huruf muqatta'ah khusus harus memakai registry profil.",
            "Tidak berlaku bila user waqaf pada kata trigger.",
        ),
        expected_features={
            "assimilation": True,
            "nasalization": True,
            "nominal_harakat": 2,
        },
        requires_profile=True,
        source_ids=PROFILE_SOURCES + COMMON_SOURCES[:2],
    ),
    _rule(
        code="idgham_bilaghunnah",
        name="Idgham Bilaghunnah",
        family=RuleFamily.NUN_TANWIN,
        display_group=DisplayGroup.IDGHAM,
        description="Nun sakinah atau tanwin dilebur ke lam atau ra tanpa ghunnah.",
        applies_when=AppliesWhen.WASL,
        display_span_policy=DisplaySpanPolicy.TRIGGER_AND_TARGET,
        detection_maturity=DetectionMaturity.CORE_DETERMINISTIC,
        acoustic_assessment=AcousticAssessment.ASSIMILATION_MODEL,
        trigger_spec="Nun sakinah atau tanwin pada akhir unit kata.",
        context_spec="Huruf terucap berikutnya ل atau ر pada kata berikutnya.",
        exclusions=("Tidak berlaku bila user waqaf pada kata trigger.",),
        expected_features={"assimilation": True, "nasalization": False},
    ),
    _rule(
        code="iqlab",
        name="Iqlab",
        family=RuleFamily.NUN_TANWIN,
        display_group=DisplayGroup.NUN_TANWIN,
        description=(
            "Nun sakinah atau tanwin bertemu ba dan berubah menjadi mim samar "
            "dengan ghunnah."
        ),
        applies_when=AppliesWhen.CONTEXTUAL,
        display_span_policy=DisplaySpanPolicy.TRIGGER_AND_TARGET,
        detection_maturity=DetectionMaturity.CORE_DETERMINISTIC,
        acoustic_assessment=AcousticAssessment.NASALIZATION_MODEL,
        trigger_spec="Nun sakinah, tanwin, atau tanda iqlab Uthmani.",
        context_spec="Huruf terucap berikutnya ب.",
        exclusions=("Tidak berlaku lintas kata bila waqaf pada trigger.",),
        expected_features={
            "nasalization": True,
            "nominal_harakat": 2,
            "labial_transition": True,
        },
    ),
    _rule(
        code="ikhfa_haqiqi",
        name="Ikhfa Haqiqi",
        family=RuleFamily.NUN_TANWIN,
        display_group=DisplayGroup.NUN_TANWIN,
        description=(
            "Nun sakinah atau tanwin dibaca samar dengan ghunnah sebelum salah "
            "satu huruf ikhfa."
        ),
        applies_when=AppliesWhen.CONTEXTUAL,
        display_span_policy=DisplaySpanPolicy.TRIGGER_AND_TARGET,
        detection_maturity=DetectionMaturity.CORE_DETERMINISTIC,
        acoustic_assessment=AcousticAssessment.NASALIZATION_MODEL,
        trigger_spec="Nun sakinah atau tanwin.",
        context_spec="Huruf berikutnya salah satu ت ث ج د ذ ز س ش ص ض ط ظ ف ق ك.",
        exclusions=("Tidak berlaku lintas kata bila waqaf pada trigger.",),
        expected_features={"nasalization": True, "nominal_harakat": 2},
    ),

    # ================================================================
    # Mim sakinah
    # ================================================================
    _rule(
        code="izhar_shafawi",
        name="Izhar Shafawi",
        family=RuleFamily.MIM_SAKINAH,
        display_group=DisplayGroup.MIM_SAKINAH,
        description="Mim sakinah bertemu selain mim dan ba lalu dibaca jelas.",
        applies_when=AppliesWhen.CONTEXTUAL,
        display_span_policy=DisplaySpanPolicy.TRIGGER_ONLY,
        detection_maturity=DetectionMaturity.CORE_DETERMINISTIC,
        acoustic_assessment=AcousticAssessment.ARTICULATION_MODEL,
        trigger_spec="Mim ber-sukun asli.",
        context_spec="Huruf terucap berikutnya bukan م dan bukan ب.",
        exclusions=(
            "Kehati-hatian pada و dan ف adalah aspek artikulasi, bukan rule baru.",
            "Tidak berlaku lintas kata bila waqaf pada mim sakinah.",
        ),
        expected_features={"clarity": True},
    ),
    _rule(
        code="ikhfa_shafawi",
        name="Ikhfa Shafawi",
        family=RuleFamily.MIM_SAKINAH,
        display_group=DisplayGroup.MIM_SAKINAH,
        description="Mim sakinah bertemu ba dan dibaca samar dengan ghunnah.",
        applies_when=AppliesWhen.CONTEXTUAL,
        display_span_policy=DisplaySpanPolicy.TRIGGER_AND_TARGET,
        detection_maturity=DetectionMaturity.CORE_DETERMINISTIC,
        acoustic_assessment=AcousticAssessment.NASALIZATION_MODEL,
        trigger_spec="Mim ber-sukun asli.",
        context_spec="Huruf terucap berikutnya ب.",
        exclusions=("Tidak berlaku lintas kata bila waqaf pada mim sakinah.",),
        expected_features={
            "nasalization": True,
            "nominal_harakat": 2,
            "labial_transition": True,
        },
    ),
    _rule(
        code="idgham_mimi",
        name="Idgham Mimi",
        family=RuleFamily.MIM_SAKINAH,
        display_group=DisplayGroup.MIM_SAKINAH,
        description="Mim sakinah bertemu mim dan dilebur dengan ghunnah.",
        applies_when=AppliesWhen.CONTEXTUAL,
        display_span_policy=DisplaySpanPolicy.TRIGGER_AND_TARGET,
        detection_maturity=DetectionMaturity.CORE_DETERMINISTIC,
        acoustic_assessment=AcousticAssessment.NASALIZATION_MODEL,
        trigger_spec="Mim ber-sukun asli.",
        context_spec="Huruf terucap berikutnya م.",
        exclusions=("Tidak berlaku lintas kata bila waqaf pada mim sakinah.",),
        expected_features={
            "assimilation": True,
            "nasalization": True,
            "nominal_harakat": 2,
        },
    ),

    # ================================================================
    # Ghunnah dan qalqalah
    # ================================================================
    _rule(
        code="ghunnah_mushaddadah",
        name="Ghunnah Musyaddadah",
        family=RuleFamily.GHUNNAH,
        display_group=DisplayGroup.GHUNNAH,
        description="Nun atau mim bertasydid dibaca dengan ghunnah dua harakat.",
        applies_when=AppliesWhen.BOTH,
        display_span_policy=DisplaySpanPolicy.TRIGGER_ONLY,
        detection_maturity=DetectionMaturity.CORE_DETERMINISTIC,
        acoustic_assessment=AcousticAssessment.NASALIZATION_MODEL,
        trigger_spec="Grapheme نّ atau مّ, termasuk urutan mark Uthmani ekuivalen.",
        context_spec="Tidak memerlukan huruf berikutnya untuk identifikasi rule.",
        expected_features={"nasalization": True, "nominal_harakat": 2},
    ),
    _rule(
        code="qalqalah_sughra",
        name="Qalqalah Sughra",
        family=RuleFamily.QALQALAH,
        display_group=DisplayGroup.QALQALAH,
        description="Huruf qalqalah dengan sukun asli yang dibaca terus dipantulkan ringan.",
        applies_when=AppliesWhen.BOTH,
        display_span_policy=DisplaySpanPolicy.TRIGGER_ONLY,
        detection_maturity=DetectionMaturity.CORE_DETERMINISTIC,
        acoustic_assessment=AcousticAssessment.RELEASE_MODEL,
        trigger_spec="Salah satu ق ط ب ج د dengan sukun asli.",
        context_spec="Trigger bukan posisi waqaf aktual dan bukan huruf mushaddad.",
        expected_features={"release_strength": "light"},
    ),
    _rule(
        code="qalqalah_kubra",
        name="Qalqalah Kubra",
        family=RuleFamily.QALQALAH,
        display_group=DisplayGroup.QALQALAH,
        description=(
            "Huruf qalqalah non-mushaddad pada posisi waqaf dipantulkan lebih jelas."
        ),
        applies_when=AppliesWhen.WAQF,
        display_span_policy=DisplaySpanPolicy.TRIGGER_ONLY,
        detection_maturity=DetectionMaturity.DETERMINISTIC_WITH_EXCEPTIONS,
        acoustic_assessment=AcousticAssessment.RELEASE_MODEL,
        trigger_spec="Huruf akhir terucap salah satu ق ط ب ج د, non-mushaddad, pada waqaf aktual.",
        context_spec="Waqaf aktual terjadi pada akhir input/ayat; sukun dapat asli atau karena waqaf.",
        exclusions=("Jika huruf akhir bertasydid, klasifikasikan qalqalah_akbar.",),
        expected_features={"release_strength": "strong"},
    ),
    _rule(
        code="qalqalah_akbar",
        name="Qalqalah Akbar",
        family=RuleFamily.QALQALAH,
        display_group=DisplayGroup.QALQALAH,
        description=(
            "Huruf qalqalah bertasydid pada tempat waqaf memiliki pantulan terkuat."
        ),
        applies_when=AppliesWhen.WAQF,
        display_span_policy=DisplaySpanPolicy.TRIGGER_ONLY,
        detection_maturity=DetectionMaturity.EXPERT_GOLDSET_REQUIRED,
        acoustic_assessment=AcousticAssessment.RELEASE_MODEL,
        trigger_spec="Huruf akhir ق ط ب ج د bertasydid dan dibaca waqaf.",
        context_spec="Waqaf aktual pada kata trigger.",
        expected_features={"release_strength": "strongest"},
        source_ids=REFERENCE_ASSISTED_SOURCES,
    ),

    # ================================================================
    # Alif-lam dan lafz al-jalalah
    # ================================================================
    _rule(
        code="alif_lam_qamariyyah",
        name="Alif Lam Qamariyyah",
        family=RuleFamily.ALIF_LAM,
        display_group=DisplayGroup.ALIF_LAM,
        description="Lam ta'rif bertemu huruf qamariyyah sehingga lam dibaca jelas.",
        applies_when=AppliesWhen.BOTH,
        display_span_policy=DisplaySpanPolicy.TRIGGER_AND_TARGET,
        detection_maturity=DetectionMaturity.DETERMINISTIC_WITH_EXCEPTIONS,
        acoustic_assessment=AcousticAssessment.ARTICULATION_MODEL,
        trigger_spec="Hamzat wasl/alif + lam ta'rif pada awal lexical word.",
        context_spec="Huruf lexical setelah lam termasuk huruf qamariyyah.",
        exclusions=(
            "Lafz al-jalalah ditangani oleh lam_jalalah_*.",
            "Prefix و ف ب ك ل harus dipisahkan dari inti lexical word.",
        ),
    ),
    _rule(
        code="alif_lam_shamsiyyah",
        name="Alif Lam Shamsiyyah",
        family=RuleFamily.ALIF_LAM,
        display_group=DisplayGroup.ALIF_LAM,
        description="Lam ta'rif tidak dibaca dan huruf syamsiyyah sesudahnya ditasydidkan.",
        applies_when=AppliesWhen.BOTH,
        display_span_policy=DisplaySpanPolicy.TRIGGER_AND_TARGET,
        detection_maturity=DetectionMaturity.DETERMINISTIC_WITH_EXCEPTIONS,
        acoustic_assessment=AcousticAssessment.ASSIMILATION_MODEL,
        trigger_spec="Hamzat wasl/alif + lam ta'rif pada awal lexical word.",
        context_spec="Huruf lexical setelah lam termasuk ت ث د ذ ر ز س ش ص ض ط ظ ل ن.",
        exclusions=(
            "Lafz al-jalalah ditangani oleh lam_jalalah_*.",
            "Prefix و ف ب ك ل harus dipisahkan dari inti lexical word.",
        ),
        expected_features={"assimilation": True},
    ),
    _rule(
        code="lam_jalalah_tafkhim",
        name="Tafkhim Lam Jalalah",
        family=RuleFamily.LAM_JALALAH,
        display_group=DisplayGroup.TAFKHIM_TARQIQ,
        description="Lam pada lafz Allah dibaca tebal setelah fathah atau dammah.",
        applies_when=AppliesWhen.CONTEXTUAL,
        display_span_policy=DisplaySpanPolicy.TRIGGER_ONLY,
        detection_maturity=DetectionMaturity.DETERMINISTIC_WITH_EXCEPTIONS,
        acoustic_assessment=AcousticAssessment.RESONANCE_MODEL,
        trigger_spec="Lam utama pada lexical form lafz al-jalalah.",
        context_spec=(
            "Vokal terucap sebelum lafz al-jalalah adalah fathah/dammah; ketika "
            "memulai langsung pada lafz al-jalalah default tafkhim."
        ),
        exclusions=("Kasrah terucap sebelumnya menghasilkan lam_jalalah_tarqiq.",),
        expected_features={"resonance": "emphatic"},
        requires_profile=True,
    ),
    _rule(
        code="lam_jalalah_tarqiq",
        name="Tarqiq Lam Jalalah",
        family=RuleFamily.LAM_JALALAH,
        display_group=DisplayGroup.TAFKHIM_TARQIQ,
        description="Lam pada lafz Allah dibaca tipis setelah kasrah.",
        applies_when=AppliesWhen.CONTEXTUAL,
        display_span_policy=DisplaySpanPolicy.TRIGGER_ONLY,
        detection_maturity=DetectionMaturity.DETERMINISTIC_WITH_EXCEPTIONS,
        acoustic_assessment=AcousticAssessment.RESONANCE_MODEL,
        trigger_spec="Lam utama pada lexical form lafz al-jalalah.",
        context_spec="Vokal terucap sebelum lafz al-jalalah adalah kasrah.",
        exclusions=(
            "Jangan hanya membaca harakat di dalam kata Allah; konteks kata sebelumnya wajib."
        ),
        expected_features={"resonance": "light"},
        requires_profile=True,
    ),

    # ================================================================
    # Ra — detector harus memakai decision table dan exception lexicon
    # ================================================================
    _rule(
        code="ra_tafkhim",
        name="Tafkhim Ra",
        family=RuleFamily.RA,
        display_group=DisplayGroup.TAFKHIM_TARQIQ,
        description="Huruf ra dibaca tebal pada konteks yang ditetapkan profil Hafs.",
        applies_when=AppliesWhen.CONTEXTUAL,
        display_span_policy=DisplaySpanPolicy.TRIGGER_ONLY,
        detection_maturity=DetectionMaturity.EXPERT_GOLDSET_REQUIRED,
        acoustic_assessment=AcousticAssessment.RESONANCE_MODEL,
        trigger_spec="Grapheme ر dengan kondisi tafkhim dalam decision table Hafs.",
        context_spec=(
            "Mencakup ra ber-fathah/dammah dan sebagian ra sakinah; harus menilai "
            "asal kasrah, huruf isti'la sesudahnya, posisi waqaf, serta lexicon khusus."
        ),
        exclusions=(
            "Jangan implementasikan hanya dari harakat terdekat.",
            "Kasus dua wajah dipetakan ke ra_both_permitted.",
        ),
        expected_features={"resonance": "emphatic"},
        source_ids=REFERENCE_ASSISTED_SOURCES,
        requires_profile=True,
    ),
    _rule(
        code="ra_tarqiq",
        name="Tarqiq Ra",
        family=RuleFamily.RA,
        display_group=DisplayGroup.TAFKHIM_TARQIQ,
        description="Huruf ra dibaca tipis pada konteks yang ditetapkan profil Hafs.",
        applies_when=AppliesWhen.CONTEXTUAL,
        display_span_policy=DisplaySpanPolicy.TRIGGER_ONLY,
        detection_maturity=DetectionMaturity.EXPERT_GOLDSET_REQUIRED,
        acoustic_assessment=AcousticAssessment.RESONANCE_MODEL,
        trigger_spec="Grapheme ر dengan kondisi tarqiq dalam decision table Hafs.",
        context_spec=(
            "Mencakup ra ber-kasrah dan sebagian ra sakinah/waqaf; membutuhkan "
            "decision table dan lexicon pengecualian."
        ),
        exclusions=(
            "Jangan implementasikan hanya dari harakat terdekat.",
            "Kasus dua wajah dipetakan ke ra_both_permitted.",
        ),
        expected_features={"resonance": "light"},
        source_ids=REFERENCE_ASSISTED_SOURCES,
        requires_profile=True,
    ),
    _rule(
        code="ra_both_permitted",
        name="Ra Dua Wajah",
        family=RuleFamily.RA,
        display_group=DisplayGroup.TAFKHIM_TARQIQ,
        description=(
            "Pada lafaz tertentu profil membolehkan tafkhim atau tarqiq; aplikasi "
            "tidak boleh menandai salah salah satunya."
        ),
        applies_when=AppliesWhen.PROFILE_DEPENDENT,
        display_span_policy=DisplaySpanPolicy.TRIGGER_ONLY,
        detection_maturity=DetectionMaturity.EXPERT_GOLDSET_REQUIRED,
        acoustic_assessment=AcousticAssessment.RESONANCE_MODEL,
        trigger_spec="Ra pada lexicon dua wajah profil Hafs al-Shatibiyyah.",
        context_spec="Mode wasl/waqf dan lexical form harus cocok dengan registry profil.",
        expected_features={"allowed_resonance": ["emphatic", "light"]},
        source_ids=PROFILE_SOURCES,
        requires_profile=True,
    ),

    # ================================================================
    # Mad
    # ================================================================
    _rule(
        code="mad_tabii",
        name="Mad Tabi'i",
        family=RuleFamily.MADD,
        display_group=DisplayGroup.MADD,
        description="Huruf mad dasar dibaca dua harakat.",
        applies_when=AppliesWhen.BOTH,
        display_span_policy=DisplaySpanPolicy.TRIGGER_ONLY,
        detection_maturity=DetectionMaturity.CORE_DETERMINISTIC,
        acoustic_assessment=AcousticAssessment.DURATION,
        trigger_spec=(
            "Alif setelah fathah, waw sakinah setelah dammah, atau ya sakinah "
            "setelah kasrah, termasuk dagger alif yang ekuivalen."
        ),
        context_spec="Tidak diikuti sebab hamzah atau sukun yang mengubah jenis mad.",
        exclusions=(
            "Mad wajib, jaiz, lazim, arid, lin, silah, badl, tamkin, iwad, dan farq.",
        ),
        expected_features={"allowed_harakat": [2]},
    ),
    _rule(
        code="mad_badl",
        name="Mad Badl",
        family=RuleFamily.MADD,
        display_group=DisplayGroup.MADD,
        description="Hamzah mendahului huruf mad dalam satu kata dan dibaca dua harakat.",
        applies_when=AppliesWhen.BOTH,
        display_span_policy=DisplaySpanPolicy.TRIGGER_ONLY,
        detection_maturity=DetectionMaturity.DETERMINISTIC_WITH_EXCEPTIONS,
        acoustic_assessment=AcousticAssessment.DURATION,
        trigger_spec="Huruf mad yang secara lexical didahului hamzah.",
        context_spec="Urutan berada dalam satu lexical word menurut rasm/profil Hafs.",
        exclusions=("Kasus mad farq dan bentuk khusus qira'ah.",),
        expected_features={"allowed_harakat": [2]},
        requires_profile=True,
    ),
    _rule(
        code="mad_tamkin",
        name="Mad Tamkin",
        family=RuleFamily.MADD,
        display_group=DisplayGroup.MADD,
        description=(
            "Mad yang menjaga kejelasan dua ya atau dua waw pada pola tertentu, "
            "dibaca dua harakat."
        ),
        applies_when=AppliesWhen.BOTH,
        display_span_policy=DisplaySpanPolicy.PRONUNCIATION_SPAN,
        detection_maturity=DetectionMaturity.EXPERT_GOLDSET_REQUIRED,
        acoustic_assessment=AcousticAssessment.DURATION,
        trigger_spec="Pola lexical dua ya/waw yang memenuhi definisi mad tamkin.",
        context_spec="Detector memakai morphology/lexicon terverifikasi, bukan regex umum.",
        expected_features={"allowed_harakat": [2]},
        source_ids=REFERENCE_ASSISTED_SOURCES,
    ),
    _rule(
        code="mad_iwad",
        name="Mad Iwad",
        family=RuleFamily.MADD,
        display_group=DisplayGroup.MADD,
        description="Tanwin fathah diganti dengan panjang dua harakat ketika waqaf.",
        applies_when=AppliesWhen.WAQF,
        display_span_policy=DisplaySpanPolicy.TRIGGER_ONLY,
        detection_maturity=DetectionMaturity.DETERMINISTIC_WITH_EXCEPTIONS,
        acoustic_assessment=AcousticAssessment.DURATION,
        trigger_spec="Tanwin fathah pada akhir kata yang menjadi tempat waqaf.",
        context_spec="Waqaf aktual pada kata tersebut.",
        exclusions=(
            "Ta marbutah ketika waqaf berubah menjadi ha sakinah, bukan mad iwad.",
            "Kasus rasm/lexical khusus harus memakai exception registry.",
        ),
        expected_features={"allowed_harakat": [2]},
    ),
    _rule(
        code="mad_silah_qasirah",
        name="Mad Silah Qasirah",
        family=RuleFamily.MADD,
        display_group=DisplayGroup.MADD,
        description="Ha dhamir di antara dua huruf hidup dipanjangkan dua harakat saat wasl.",
        applies_when=AppliesWhen.WASL,
        display_span_policy=DisplaySpanPolicy.TRIGGER_ONLY,
        detection_maturity=DetectionMaturity.EXPERT_GOLDSET_REQUIRED,
        acoustic_assessment=AcousticAssessment.DURATION,
        trigger_spec="Ha dhamir maskulin tunggal yang memenuhi syarat silah.",
        context_spec="Didahului dan diikuti bunyi hidup; huruf berikutnya bukan hamzah.",
        exclusions=(
            "Ha asli dalam akar kata.",
            "Ha pada lafz al-jalalah.",
            "Lexical exceptions Hafs dan kondisi waqaf.",
        ),
        expected_features={"allowed_harakat": [2]},
        source_ids=REFERENCE_ASSISTED_SOURCES,
        requires_profile=True,
    ),
    _rule(
        code="mad_silah_tawilah",
        name="Mad Silah Tawilah",
        family=RuleFamily.MADD,
        display_group=DisplayGroup.MADD,
        description="Ha dhamir memenuhi syarat silah dan diikuti hamzah pada kata berikutnya.",
        applies_when=AppliesWhen.WASL,
        display_span_policy=DisplaySpanPolicy.TRIGGER_AND_TARGET,
        detection_maturity=DetectionMaturity.EXPERT_GOLDSET_REQUIRED,
        acoustic_assessment=AcousticAssessment.DURATION,
        trigger_spec="Ha dhamir maskulin tunggal yang memenuhi syarat silah.",
        context_spec="Huruf terucap berikutnya hamzah pada kata berikutnya.",
        exclusions=(
            "Ha asli, lafz al-jalalah, lexical exceptions, dan kondisi waqaf."
        ),
        expected_features={"allowed_harakat": [4, 5], "default_harakat": 4},
        source_ids=REFERENCE_ASSISTED_SOURCES + ("HAFS_SHATIBIYYAH_PROFILE",),
        requires_profile=True,
    ),
    _rule(
        code="mad_wajib_muttasil",
        name="Mad Wajib Muttasil",
        family=RuleFamily.MADD,
        display_group=DisplayGroup.MADD,
        description="Huruf mad bertemu hamzah dalam satu kata.",
        applies_when=AppliesWhen.BOTH,
        display_span_policy=DisplaySpanPolicy.TRIGGER_AND_TARGET,
        detection_maturity=DetectionMaturity.CORE_DETERMINISTIC,
        acoustic_assessment=AcousticAssessment.DURATION,
        trigger_spec="Huruf mad valid.",
        context_spec="Hamzah terucap muncul sesudahnya dalam lexical word yang sama.",
        expected_features={
            "allowed_harakat": [4, 5],
            "default_harakat": 4,
            "consistency_group": "muttasil_munfasil_silah_tawilah",
        },
        requires_profile=True,
        source_ids=PROFILE_SOURCES + COMMON_SOURCES[:2],
    ),
    _rule(
        code="mad_jaiz_munfasil",
        name="Mad Jaiz Munfasil",
        family=RuleFamily.MADD,
        display_group=DisplayGroup.MADD,
        description="Huruf mad di akhir kata bertemu hamzah pada kata berikutnya saat wasl.",
        applies_when=AppliesWhen.WASL,
        display_span_policy=DisplaySpanPolicy.TRIGGER_AND_TARGET,
        detection_maturity=DetectionMaturity.CORE_DETERMINISTIC,
        acoustic_assessment=AcousticAssessment.DURATION,
        trigger_spec="Huruf mad berada pada akhir bunyi kata pertama.",
        context_spec="Huruf terucap awal kata berikutnya adalah hamzah.",
        exclusions=("Tidak berlaku bila waqaf pada kata pertama.",),
        expected_features={
            "allowed_harakat": [4, 5],
            "default_harakat": 4,
            "consistency_group": "muttasil_munfasil_silah_tawilah",
        },
        requires_profile=True,
        source_ids=PROFILE_SOURCES + COMMON_SOURCES[:2],
    ),
    _rule(
        code="mad_lazim_kalimi_muthaqqal",
        name="Mad Lazim Kalimi Muthaqqal",
        family=RuleFamily.MADD,
        display_group=DisplayGroup.MADD,
        description="Huruf mad bertemu huruf bertasydid dalam satu kata dan dibaca enam harakat.",
        applies_when=AppliesWhen.BOTH,
        display_span_policy=DisplaySpanPolicy.TRIGGER_AND_TARGET,
        detection_maturity=DetectionMaturity.CORE_DETERMINISTIC,
        acoustic_assessment=AcousticAssessment.DURATION,
        trigger_spec="Huruf mad valid.",
        context_spec="Huruf terucap setelahnya bertasydid dalam lexical word yang sama.",
        expected_features={"allowed_harakat": [6]},
    ),
    _rule(
        code="mad_lazim_kalimi_mukhaffaf",
        name="Mad Lazim Kalimi Mukhaffaf",
        family=RuleFamily.MADD,
        display_group=DisplayGroup.MADD,
        description="Huruf mad bertemu sukun asli tanpa tasydid dalam satu kata.",
        applies_when=AppliesWhen.BOTH,
        display_span_policy=DisplaySpanPolicy.TRIGGER_AND_TARGET,
        detection_maturity=DetectionMaturity.DETERMINISTIC_WITH_EXCEPTIONS,
        acoustic_assessment=AcousticAssessment.DURATION,
        trigger_spec="Huruf mad valid.",
        context_spec="Huruf setelahnya memiliki sukun asli tanpa tasydid dalam satu kata.",
        exclusions=("Lexical scope sangat terbatas dan wajib diuji terhadap gold set.",),
        expected_features={"allowed_harakat": [6]},
        source_ids=REFERENCE_ASSISTED_SOURCES,
    ),
    _rule(
        code="mad_lazim_harfi_muthaqqal",
        name="Mad Lazim Harfi Muthaqqal",
        family=RuleFamily.MADD,
        display_group=DisplayGroup.MADD,
        description="Mad pada huruf muqatta'ah dengan idgham/tasydid dibaca enam harakat.",
        applies_when=AppliesWhen.PROFILE_DEPENDENT,
        display_span_policy=DisplaySpanPolicy.PRONUNCIATION_SPAN,
        detection_maturity=DetectionMaturity.EXPERT_GOLDSET_REQUIRED,
        acoustic_assessment=AcousticAssessment.DURATION,
        trigger_spec="Huruf muqatta'ah yang memiliki struktur mad lazim harfi.",
        context_spec="Ejaan nama huruf menghasilkan sukun lalu terasimilasi pada huruf berikutnya.",
        expected_features={"allowed_harakat": [6]},
        requires_profile=True,
        source_ids=PROFILE_SOURCES,
    ),
    _rule(
        code="mad_lazim_harfi_mukhaffaf",
        name="Mad Lazim Harfi Mukhaffaf",
        family=RuleFamily.MADD,
        display_group=DisplayGroup.MADD,
        description="Mad pada huruf muqatta'ah tanpa idgham dibaca enam harakat.",
        applies_when=AppliesWhen.PROFILE_DEPENDENT,
        display_span_policy=DisplaySpanPolicy.PRONUNCIATION_SPAN,
        detection_maturity=DetectionMaturity.EXPERT_GOLDSET_REQUIRED,
        acoustic_assessment=AcousticAssessment.DURATION,
        trigger_spec="Huruf muqatta'ah yang memiliki struktur mad lazim harfi.",
        context_spec="Ejaan nama huruf menghasilkan mad diikuti sukun asli tanpa idgham.",
        expected_features={"allowed_harakat": [6]},
        requires_profile=True,
        source_ids=PROFILE_SOURCES,
    ),
    _rule(
        code="mad_harfi_tabii",
        name="Mad Harfi Tabi'i",
        family=RuleFamily.MADD,
        display_group=DisplayGroup.MADD,
        description="Huruf muqatta'ah kelompok حي طهر dibaca dua harakat.",
        applies_when=AppliesWhen.PROFILE_DEPENDENT,
        display_span_policy=DisplaySpanPolicy.PRONUNCIATION_SPAN,
        detection_maturity=DetectionMaturity.DETERMINISTIC_WITH_EXCEPTIONS,
        acoustic_assessment=AcousticAssessment.DURATION,
        trigger_spec="Huruf muqatta'ah yang nama hurufnya terdiri dari dua komponen suara.",
        context_spec="Registry huruf muqatta'ah profil Hafs.",
        expected_features={"allowed_harakat": [2]},
        requires_profile=True,
        source_ids=PROFILE_SOURCES,
    ),
    _rule(
        code="mad_ayn_muqattaah",
        name="Mad 'Ayn Muqatta'ah",
        family=RuleFamily.MADD,
        display_group=DisplayGroup.MADD,
        description="Huruf عين pada pembuka surah memiliki pilihan empat atau enam harakat.",
        applies_when=AppliesWhen.PROFILE_DEPENDENT,
        display_span_policy=DisplaySpanPolicy.PRONUNCIATION_SPAN,
        detection_maturity=DetectionMaturity.EXPERT_GOLDSET_REQUIRED,
        acoustic_assessment=AcousticAssessment.DURATION,
        trigger_spec="Huruf muqatta'ah عين pada lokasi yang ditetapkan profil.",
        context_spec="Pembuka surah terkait dan profil Hafs al-Shatibiyyah.",
        expected_features={"allowed_harakat": [4, 6], "default_harakat": 6},
        requires_profile=True,
        source_ids=PROFILE_SOURCES,
    ),
    _rule(
        code="mad_farq",
        name="Mad Farq",
        family=RuleFamily.MADD,
        display_group=DisplayGroup.MADD,
        description="Hamzah istifham masuk pada hamzat wasl dan dibaca panjang enam harakat.",
        applies_when=AppliesWhen.PROFILE_DEPENDENT,
        display_span_policy=DisplaySpanPolicy.PRONUNCIATION_SPAN,
        detection_maturity=DetectionMaturity.EXPERT_GOLDSET_REQUIRED,
        acoustic_assessment=AcousticAssessment.DURATION,
        trigger_spec="Lexical forms mad farq yang ditetapkan riwayah Hafs.",
        context_spec="Hamzah pertanyaan + hamzat wasl dengan wajah bacaan profil.",
        expected_features={"allowed_harakat": [6]},
        requires_profile=True,
        source_ids=PROFILE_SOURCES,
    ),
    _rule(
        code="mad_arid_lissukun",
        name="Mad 'Arid Lissukun",
        family=RuleFamily.MADD,
        display_group=DisplayGroup.MADD,
        description="Huruf mad sebelum huruf yang dimatikan karena waqaf dapat dibaca 2, 4, atau 6.",
        applies_when=AppliesWhen.WAQF,
        display_span_policy=DisplaySpanPolicy.PRONUNCIATION_SPAN,
        detection_maturity=DetectionMaturity.CORE_DETERMINISTIC,
        acoustic_assessment=AcousticAssessment.DURATION,
        trigger_spec="Huruf mad valid sebelum konsonan akhir berharakat.",
        context_spec="Waqaf aktual menyebabkan konsonan akhir menjadi sukun.",
        exclusions=("Jika pola memenuhi mad lin, gunakan mad_lin.",),
        expected_features={
            "allowed_harakat": [2, 4, 6],
            "consistency_group": "waqf_arid_lin",
        },
        requires_profile=True,
    ),
    _rule(
        code="mad_lin",
        name="Mad Lin",
        family=RuleFamily.MADD,
        display_group=DisplayGroup.MADD,
        description="Waw/ya sakinah setelah fathah dipanjangkan saat waqaf.",
        applies_when=AppliesWhen.WAQF,
        display_span_policy=DisplaySpanPolicy.PRONUNCIATION_SPAN,
        detection_maturity=DetectionMaturity.CORE_DETERMINISTIC,
        acoustic_assessment=AcousticAssessment.DURATION,
        trigger_spec="Waw atau ya sakinah yang didahului fathah.",
        context_spec="Terdapat konsonan sesudahnya yang menjadi sukun karena waqaf.",
        expected_features={
            "allowed_harakat": [2, 4, 6],
            "consistency_group": "waqf_arid_lin",
        },
        requires_profile=True,
    ),

    # ================================================================
    # Idgham selain nun/tanwin dan mim sakinah
    # ================================================================
    _rule(
        code="idgham_mutamathilain",
        name="Idgham Mutamathilain",
        family=RuleFamily.IDGHAM,
        display_group=DisplayGroup.IDGHAM,
        description="Huruf pertama sakinah bertemu huruf kedua yang sama dan dilebur.",
        applies_when=AppliesWhen.CONTEXTUAL,
        display_span_policy=DisplaySpanPolicy.TRIGGER_AND_TARGET,
        detection_maturity=DetectionMaturity.DETERMINISTIC_WITH_EXCEPTIONS,
        acoustic_assessment=AcousticAssessment.ASSIMILATION_MODEL,
        trigger_spec="Konsonan sakinah.",
        context_spec="Konsonan terucap berikutnya identik dan memenuhi tabel Hafs.",
        exclusions=(
            "Mim+mim ditangani idgham_mimi.",
            "Nun/tanwin ditangani keluarga nun_tanwin.",
            "Huruf mad tidak boleh dipakai sebagai trigger konsonan idgham.",
        ),
        expected_features={"assimilation": True},
        source_ids=REFERENCE_ASSISTED_SOURCES,
    ),
    _rule(
        code="idgham_mutajanisain",
        name="Idgham Mutajanisain",
        family=RuleFamily.IDGHAM,
        display_group=DisplayGroup.IDGHAM,
        description="Dua huruf semakhraj dengan sifat berbeda dilebur pada pasangan tertentu.",
        applies_when=AppliesWhen.CONTEXTUAL,
        display_span_policy=DisplaySpanPolicy.TRIGGER_AND_TARGET,
        detection_maturity=DetectionMaturity.EXPERT_GOLDSET_REQUIRED,
        acoustic_assessment=AcousticAssessment.ASSIMILATION_MODEL,
        trigger_spec="Huruf pertama sakinah pada exact-pair table riwayah Hafs.",
        context_spec="Huruf berikutnya pasangan mutajanisain yang diizinkan profil.",
        exclusions=(
            "Jangan memakai daftar semua huruf yang sekadar dekat makhraj.",
            "Gunakan exact-pair table dan lexical exceptions terverifikasi."
        ),
        expected_features={"assimilation": True},
        requires_profile=True,
        source_ids=PROFILE_SOURCES,
    ),
    _rule(
        code="idgham_mutaqaribain",
        name="Idgham Mutaqaribain",
        family=RuleFamily.IDGHAM,
        display_group=DisplayGroup.IDGHAM,
        description="Dua huruf berdekatan makhraj/sifat dilebur pada pasangan tertentu.",
        applies_when=AppliesWhen.CONTEXTUAL,
        display_span_policy=DisplaySpanPolicy.TRIGGER_AND_TARGET,
        detection_maturity=DetectionMaturity.EXPERT_GOLDSET_REQUIRED,
        acoustic_assessment=AcousticAssessment.ASSIMILATION_MODEL,
        trigger_spec="Huruf pertama sakinah pada exact-pair table riwayah Hafs.",
        context_spec="Huruf berikutnya pasangan mutaqaribain yang diizinkan profil.",
        exclusions=(
            "Kasus قْ + ك membutuhkan metadata idgham kamil/naqis sesuai profil.",
            "Gunakan exact-pair table dan lexical exceptions terverifikasi."
        ),
        expected_features={"assimilation": True},
        requires_profile=True,
        source_ids=PROFILE_SOURCES,
    ),

    # ================================================================
    # Orthographic pronunciation aids
    # ================================================================
    _rule(
        code="hamzat_wasl",
        name="Hamzat Wasl",
        family=RuleFamily.ORTHOGRAPHIC,
        display_group=DisplayGroup.ORTHOGRAPHIC,
        description="Hamzat wasl dibaca ketika ibtida dan gugur ketika wasl.",
        applies_when=AppliesWhen.CONTEXTUAL,
        display_span_policy=DisplaySpanPolicy.MARK_ONLY,
        detection_maturity=DetectionMaturity.CORE_DETERMINISTIC,
        acoustic_assessment=AcousticAssessment.RENDER_ONLY,
        trigger_spec="Grapheme ٱ atau orthographic equivalent yang tervalidasi.",
        context_spec="Status dibaca/tidak dibaca ditentukan oleh ibtida atau wasl.",
        expected_features={"render_only": True},
    ),
    _rule(
        code="silent_letter",
        name="Huruf Tidak Dibaca",
        family=RuleFamily.ORTHOGRAPHIC,
        display_group=DisplayGroup.ORTHOGRAPHIC,
        description="Tanda atau huruf rasm tertentu tidak dilafalkan pada konteks bacaan.",
        applies_when=AppliesWhen.CONTEXTUAL,
        display_span_policy=DisplaySpanPolicy.MARK_ONLY,
        detection_maturity=DetectionMaturity.REFERENCE_ASSISTED,
        acoustic_assessment=AcousticAssessment.RENDER_ONLY,
        trigger_spec="Orthographic mark/letter yang ditandai silent oleh script profile.",
        context_spec="Makna silent bergantung wasl/waqf dan exact script resource.",
        exclusions=(
            "Jangan menyimpulkan silent hanya dari bentuk Unicode tanpa script profile."
        ),
        expected_features={"render_only": True},
        source_ids=REFERENCE_ASSISTED_SOURCES,
        requires_profile=True,
    ),

    # ================================================================
    # Saktah profil Hafs
    # ================================================================
    _rule(
        code="saktah_wajibah",
        name="Saktah Wajibah",
        family=RuleFamily.WAQF,
        display_group=DisplayGroup.WAQF,
        description="Berhenti sangat singkat tanpa mengambil napas pada lokasi wajib profil.",
        applies_when=AppliesWhen.PROFILE_DEPENDENT,
        display_span_policy=DisplaySpanPolicy.MARK_ONLY,
        detection_maturity=DetectionMaturity.DETERMINISTIC_WITH_EXCEPTIONS,
        acoustic_assessment=AcousticAssessment.PAUSE,
        trigger_spec="Boundary location yang terdaftar mandatory_saktah pada profil.",
        context_spec="Bacaan disambung melewati boundary tersebut.",
        expected_features={
            "pause_required": True,
            "breath_allowed": False,
            "pause_duration_class": "very_short",
        },
        requires_profile=True,
        source_ids=PROFILE_SOURCES,
    ),
    _rule(
        code="saktah_jaizah",
        name="Saktah Jaizah",
        family=RuleFamily.WAQF,
        display_group=DisplayGroup.WAQF,
        description="Saktah yang dibolehkan pada lokasi khusus profil, bukan kewajiban umum.",
        applies_when=AppliesWhen.PROFILE_DEPENDENT,
        display_span_policy=DisplaySpanPolicy.MARK_ONLY,
        detection_maturity=DetectionMaturity.EXPERT_GOLDSET_REQUIRED,
        acoustic_assessment=AcousticAssessment.PAUSE,
        trigger_spec="Boundary location yang terdaftar optional_saktah pada profil.",
        context_spec="Mode bacaan lintas ayat/surah dan pilihan wajah bacaan user.",
        expected_features={
            "pause_optional": True,
            "breath_allowed": False,
            "pause_duration_class": "very_short",
        },
        requires_profile=True,
        source_ids=PROFILE_SOURCES,
    ),
)


RULE_SPECS = MappingProxyType({rule.code: rule for rule in _RULES})
validate_rule_specs(RULE_SPECS)


EXPECTED_RULE_CODES = frozenset(
    {
        "izhar_halqi",
        "izhar_mutlaq",
        "idgham_bighunnah",
        "idgham_bilaghunnah",
        "iqlab",
        "ikhfa_haqiqi",
        "izhar_shafawi",
        "ikhfa_shafawi",
        "idgham_mimi",
        "ghunnah_mushaddadah",
        "qalqalah_sughra",
        "qalqalah_kubra",
        "qalqalah_akbar",
        "alif_lam_qamariyyah",
        "alif_lam_shamsiyyah",
        "lam_jalalah_tafkhim",
        "lam_jalalah_tarqiq",
        "ra_tafkhim",
        "ra_tarqiq",
        "ra_both_permitted",
        "mad_tabii",
        "mad_badl",
        "mad_tamkin",
        "mad_iwad",
        "mad_silah_qasirah",
        "mad_silah_tawilah",
        "mad_wajib_muttasil",
        "mad_jaiz_munfasil",
        "mad_lazim_kalimi_muthaqqal",
        "mad_lazim_kalimi_mukhaffaf",
        "mad_lazim_harfi_muthaqqal",
        "mad_lazim_harfi_mukhaffaf",
        "mad_harfi_tabii",
        "mad_ayn_muqattaah",
        "mad_farq",
        "mad_arid_lissukun",
        "mad_lin",
        "idgham_mutamathilain",
        "idgham_mutajanisain",
        "idgham_mutaqaribain",
        "hamzat_wasl",
        "silent_letter",
        "saktah_wajibah",
        "saktah_jaizah",
    }
)

if set(RULE_SPECS) != EXPECTED_RULE_CODES:
    raise RuntimeError(
        "RULE_SPECS tidak sama dengan EXPECTED_RULE_CODES. "
        f"missing={sorted(EXPECTED_RULE_CODES - set(RULE_SPECS))}, "
        f"extra={sorted(set(RULE_SPECS) - EXPECTED_RULE_CODES)}"
    )


def get_rule_spec(code: str) -> TajwidRuleSpec:
    try:
        return RULE_SPECS[code]
    except KeyError as exc:
        raise KeyError(f"Tajwid v3 rule '{code}' tidak terdaftar.") from exc


def iter_rule_specs() -> Tuple[TajwidRuleSpec, ...]:
    return tuple(sorted(RULE_SPECS.values(), key=lambda item: item.code))
