from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple


SPECIFICATION_VERSION = "3.0.0-alpha.1"
DEFAULT_RECITATION_PROFILE_ID = "hafs_asim_shatibiyyah"
DEFAULT_READING_MODE = "ayah_stop"


class ReadingMode(str, Enum):
    """Cara hubungan bacaan yang memengaruhi hukum kontekstual."""

    AYAH_STOP = "ayah_stop"
    WASL = "wasl"
    WAQF = "waqf"


class AppliesWhen(str, Enum):
    WASL = "wasl"
    WAQF = "waqf"
    BOTH = "both"
    PROFILE_DEPENDENT = "profile_dependent"
    CONTEXTUAL = "contextual"


class RuleFamily(str, Enum):
    NUN_TANWIN = "nun_tanwin"
    MIM_SAKINAH = "mim_sakinah"
    GHUNNAH = "ghunnah"
    QALQALAH = "qalqalah"
    ALIF_LAM = "alif_lam"
    LAM_JALALAH = "lam_jalalah"
    RA = "ra"
    MADD = "madd"
    IDGHAM = "idgham"
    ORTHOGRAPHIC = "orthographic"
    WAQF = "waqf"


class DisplayGroup(str, Enum):
    REGULAR = "regular"
    NUN_TANWIN = "nun_tanwin"
    MIM_SAKINAH = "mim_sakinah"
    GHUNNAH = "ghunnah"
    QALQALAH = "qalqalah"
    ALIF_LAM = "alif_lam"
    TAFKHIM_TARQIQ = "tafkhim_tarqiq"
    MADD = "mad"
    IDGHAM = "idgham"
    ORTHOGRAPHIC = "orthographic"
    WAQF = "waqf"


class DisplaySpanPolicy(str, Enum):
    """
    Rentang yang diwarnai frontend.

    Trigger dan context tetap harus disimpan terpisah oleh engine. Kebijakan
    display tidak boleh dipakai untuk menyimpulkan rentang audio penilaian.
    """

    TRIGGER_ONLY = "trigger_only"
    TRIGGER_AND_TARGET = "trigger_and_target"
    PRONUNCIATION_SPAN = "pronunciation_span"
    MARK_ONLY = "mark_only"


class DetectionMaturity(str, Enum):
    """Tingkat kesiapan detector berbasis teks untuk Engine v3."""

    CORE_DETERMINISTIC = "core_deterministic"
    DETERMINISTIC_WITH_EXCEPTIONS = "deterministic_with_exceptions"
    REFERENCE_ASSISTED = "reference_assisted"
    EXPERT_GOLDSET_REQUIRED = "expert_goldset_required"


class AcousticAssessment(str, Enum):
    """Kesiapan rule untuk dinilai dari audio user."""

    DURATION = "duration"
    NASALIZATION_MODEL = "nasalization_model"
    RELEASE_MODEL = "release_model"
    ASSIMILATION_MODEL = "assimilation_model"
    RESONANCE_MODEL = "resonance_model"
    ARTICULATION_MODEL = "articulation_model"
    PAUSE = "pause"
    RENDER_ONLY = "render_only"
    DEFERRED = "deferred"


class VerificationState(str, Enum):
    PROVISIONAL = "provisional"
    REFERENCE_CHECKED = "reference_checked"
    EXPERT_VERIFIED = "expert_verified"


@dataclass(frozen=True, slots=True)
class SourceReference:
    source_id: str
    title: str
    role: str
    authority_level: str
    notes: str = ""


@dataclass(frozen=True, slots=True)
class MaddSetting:
    code: str
    allowed_harakat: Tuple[int, ...]
    default_harakat: Optional[int]
    consistency_group: Optional[str] = None
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.allowed_harakat:
            raise ValueError(f"Madd setting '{self.code}' harus memiliki nilai.")
        if any(value <= 0 for value in self.allowed_harakat):
            raise ValueError(f"Madd setting '{self.code}' memiliki nilai invalid.")
        if self.default_harakat is not None:
            if self.default_harakat not in self.allowed_harakat:
                raise ValueError(
                    f"Default {self.default_harakat} tidak termasuk allowed "
                    f"untuk '{self.code}'."
                )


@dataclass(frozen=True, slots=True)
class BoundaryLocation:
    """Lokasi hukum yang terjadi pada batas kata atau ayat."""

    start_verse_key: str
    start_word: str
    end_verse_key: str
    end_word: str
    notes: str = ""


@dataclass(frozen=True, slots=True)
class RecitationProfile:
    profile_id: str
    qiraah: str
    riwayah: str
    tariq: str
    script_profile: str
    default_reading_mode: ReadingMode
    madd_settings: Mapping[str, MaddSetting]
    mandatory_saktah: Tuple[BoundaryLocation, ...] = ()
    optional_saktah: Tuple[BoundaryLocation, ...] = ()
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.profile_id.strip():
            raise ValueError("profile_id wajib diisi.")
        if not self.madd_settings:
            raise ValueError("Recitation profile wajib memiliki madd_settings.")
        object.__setattr__(
            self,
            "madd_settings",
            MappingProxyType(dict(self.madd_settings)),
        )


@dataclass(frozen=True, slots=True)
class TajwidRuleSpec:
    code: str
    name: str
    family: RuleFamily
    display_group: DisplayGroup
    description: str
    applies_when: AppliesWhen
    display_span_policy: DisplaySpanPolicy
    detection_maturity: DetectionMaturity
    acoustic_assessment: AcousticAssessment
    trigger_spec: str
    context_spec: str
    exclusions: Tuple[str, ...] = ()
    expected_features: Mapping[str, Any] = field(default_factory=dict)
    requires_profile: bool = False
    verification_state: VerificationState = VerificationState.PROVISIONAL
    source_ids: Tuple[str, ...] = ()
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.code or any(ch not in "abcdefghijklmnopqrstuvwxyz0123456789_" for ch in self.code):
            raise ValueError(
                f"Rule code '{self.code}' hanya boleh memakai lowercase, angka, underscore."
            )
        if not self.name.strip():
            raise ValueError(f"Rule '{self.code}' harus memiliki nama.")
        if not self.description.strip():
            raise ValueError(f"Rule '{self.code}' harus memiliki deskripsi.")
        if not self.trigger_spec.strip():
            raise ValueError(f"Rule '{self.code}' harus memiliki trigger_spec.")
        if not self.context_spec.strip():
            raise ValueError(f"Rule '{self.code}' harus memiliki context_spec.")
        object.__setattr__(
            self,
            "expected_features",
            MappingProxyType(dict(self.expected_features)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "family": self.family.value,
            "display_group": self.display_group.value,
            "description": self.description,
            "applies_when": self.applies_when.value,
            "display_span_policy": self.display_span_policy.value,
            "detection_maturity": self.detection_maturity.value,
            "acoustic_assessment": self.acoustic_assessment.value,
            "trigger_spec": self.trigger_spec,
            "context_spec": self.context_spec,
            "exclusions": list(self.exclusions),
            "expected_features": dict(self.expected_features),
            "requires_profile": self.requires_profile,
            "verification_state": self.verification_state.value,
            "source_ids": list(self.source_ids),
            "notes": self.notes,
        }


SOURCE_REFERENCES: Mapping[str, SourceReference] = MappingProxyType(
    {
        "QUL_QPC_HAFS_TAJWEED": SourceReference(
            source_id="QUL_QPC_HAFS_TAJWEED",
            title="Quranic Universal Library — QPC Hafs Tajweed",
            role=(
                "Referensi teks dan visual tajwid untuk perbandingan corpus, "
                "bukan oracle tunggal."
            ),
            authority_level="curated_reference",
            notes=(
                "QUL menyediakan resource QPC Hafs Tajweed dan annotation tool."
            ),
        ),
        "QURAN_FOUNDATION_TAJWEED_V4": SourceReference(
            source_id="QURAN_FOUNDATION_TAJWEED_V4",
            title="Quran Foundation — Tajweed V4 Mushaf",
            role="Referensi visual glyph berwarna untuk validasi hasil render.",
            authority_level="curated_reference",
        ),
        "QURAN_TAJWEED_JSON_LEGACY": SourceReference(
            source_id="QURAN_TAJWEED_JSON_LEGACY",
            title="cpfair/quran-tajweed Hafs annotations",
            role=(
                "Dataset pembanding exact-span untuk bootstrap gold set; "
                "tidak dipakai langsung tanpa text alignment."
            ),
            authority_level="secondary_dataset",
            notes=(
                "Project tidak aktif dan offset bergantung pada versi teks Uthmani."
            ),
        ),
        "HAFS_SHATIBIYYAH_PROFILE": SourceReference(
            source_id="HAFS_SHATIBIYYAH_PROFILE",
            title="Hafs 'an 'Asim melalui Tariq al-Shatibiyyah",
            role=(
                "Mengunci pilihan bacaan yang memengaruhi panjang mad, saktah, "
                "dan bacaan khusus."
            ),
            authority_level="recitation_profile",
        ),
        "EXPERT_TALAQQI_REVIEW": SourceReference(
            source_id="EXPERT_TALAQQI_REVIEW",
            title="Validasi ahli tajwid bersanad/berijazah",
            role=(
                "Oracle final untuk kasus kompleks, pengecualian, dan penilaian "
                "false positive/false negative."
            ),
            authority_level="final_review",
        ),
    }
)


_DEFAULT_MADD_SETTINGS = {
    "mad_tabii": MaddSetting(
        code="mad_tabii",
        allowed_harakat=(2,),
        default_harakat=2,
    ),
    "mad_badl": MaddSetting(
        code="mad_badl",
        allowed_harakat=(2,),
        default_harakat=2,
    ),
    "mad_tamkin": MaddSetting(
        code="mad_tamkin",
        allowed_harakat=(2,),
        default_harakat=2,
    ),
    "mad_iwad": MaddSetting(
        code="mad_iwad",
        allowed_harakat=(2,),
        default_harakat=2,
    ),
    "mad_silah_qasirah": MaddSetting(
        code="mad_silah_qasirah",
        allowed_harakat=(2,),
        default_harakat=2,
    ),
    "mad_silah_tawilah": MaddSetting(
        code="mad_silah_tawilah",
        allowed_harakat=(4, 5),
        default_harakat=4,
        consistency_group="muttasil_munfasil_silah_tawilah",
    ),
    "mad_wajib_muttasil": MaddSetting(
        code="mad_wajib_muttasil",
        allowed_harakat=(4, 5),
        default_harakat=4,
        consistency_group="muttasil_munfasil_silah_tawilah",
    ),
    "mad_jaiz_munfasil": MaddSetting(
        code="mad_jaiz_munfasil",
        allowed_harakat=(4, 5),
        default_harakat=4,
        consistency_group="muttasil_munfasil_silah_tawilah",
    ),
    "mad_lazim": MaddSetting(
        code="mad_lazim",
        allowed_harakat=(6,),
        default_harakat=6,
    ),
    "mad_ayn_muqattaah": MaddSetting(
        code="mad_ayn_muqattaah",
        allowed_harakat=(4, 6),
        default_harakat=6,
        notes="Khusus huruf عين pada huruf muqatta'ah menurut profil.",
    ),
    "mad_arid_lissukun": MaddSetting(
        code="mad_arid_lissukun",
        allowed_harakat=(2, 4, 6),
        default_harakat=2,
        consistency_group="waqf_arid_lin",
    ),
    "mad_lin": MaddSetting(
        code="mad_lin",
        allowed_harakat=(2, 4, 6),
        default_harakat=2,
        consistency_group="waqf_arid_lin",
    ),
    "mad_farq": MaddSetting(
        code="mad_farq",
        allowed_harakat=(6,),
        default_harakat=6,
    ),
}


HAFS_ASIM_SHATIBIYYAH_PROFILE = RecitationProfile(
    profile_id=DEFAULT_RECITATION_PROFILE_ID,
    qiraah="Asim",
    riwayah="Hafs",
    tariq="al-Shatibiyyah",
    script_profile="QPC Hafs / Uthmani-compatible",
    default_reading_mode=ReadingMode.AYAH_STOP,
    madd_settings=_DEFAULT_MADD_SETTINGS,
    mandatory_saktah=(
        BoundaryLocation(
            start_verse_key="18:1",
            start_word="عِوَجَا",
            end_verse_key="18:2",
            end_word="قَيِّمًا",
            notes="Saktah pada batas dua ayat ketika disambung.",
        ),
        BoundaryLocation(
            start_verse_key="36:52",
            start_word="مَرْقَدِنَا",
            end_verse_key="36:52",
            end_word="هَذَا",
        ),
        BoundaryLocation(
            start_verse_key="75:27",
            start_word="مَنْ",
            end_verse_key="75:27",
            end_word="رَاقٍ",
        ),
        BoundaryLocation(
            start_verse_key="83:14",
            start_word="بَلْ",
            end_verse_key="83:14",
            end_word="رَانَ",
        ),
    ),
    optional_saktah=(
        BoundaryLocation(
            start_verse_key="69:28",
            start_word="مَالِيَهْ",
            end_verse_key="69:29",
            end_word="هَلَكَ",
            notes="Tidak diaktifkan pada MVP detector tanpa review ahli.",
        ),
        BoundaryLocation(
            start_verse_key="8:75",
            start_word="عَلِيمٌ",
            end_verse_key="9:1",
            end_word="بَرَاءَةٌ",
            notes="Kasus lintas surah; di luar mode ayah_stop biasa.",
        ),
    ),
    notes=(
        "Default aplikasi menggunakan 4 harakat untuk mad yang memiliki opsi "
        "4/5, tetapi evaluator harus menerima nilai yang diizinkan profil dan "
        "menilai konsistensi dalam satu sesi."
    ),
)


RECITATION_PROFILES: Mapping[str, RecitationProfile] = MappingProxyType(
    {HAFS_ASIM_SHATIBIYYAH_PROFILE.profile_id: HAFS_ASIM_SHATIBIYYAH_PROFILE}
)


def get_recitation_profile(
    profile_id: str = DEFAULT_RECITATION_PROFILE_ID,
) -> RecitationProfile:
    try:
        return RECITATION_PROFILES[profile_id]
    except KeyError as exc:
        raise KeyError(f"Recitation profile '{profile_id}' tidak terdaftar.") from exc


def validate_rule_specs(
    rules: Mapping[str, TajwidRuleSpec],
    *,
    source_references: Mapping[str, SourceReference] = SOURCE_REFERENCES,
) -> None:
    if not rules:
        raise ValueError("Rule specification tidak boleh kosong.")

    for code, rule in rules.items():
        if code != rule.code:
            raise ValueError(
                f"Key '{code}' tidak sama dengan rule.code '{rule.code}'."
            )
        unknown_sources = set(rule.source_ids) - set(source_references)
        if unknown_sources:
            raise ValueError(
                f"Rule '{code}' memakai source_id tidak dikenal: "
                f"{sorted(unknown_sources)}"
            )
        if rule.display_group == DisplayGroup.REGULAR:
            raise ValueError(
                "regular adalah render gap, bukan TajwidRuleSpec database."
            )


def rule_specs_as_dict(
    rules: Mapping[str, TajwidRuleSpec],
) -> Dict[str, Dict[str, Any]]:
    validate_rule_specs(rules)
    return {code: rule.to_dict() for code, rule in rules.items()}


def assert_expected_rule_codes(
    rules: Mapping[str, TajwidRuleSpec],
    expected_codes: Iterable[str],
) -> None:
    missing = set(expected_codes) - set(rules)
    if missing:
        raise AssertionError(f"Rule wajib belum terdaftar: {sorted(missing)}")
