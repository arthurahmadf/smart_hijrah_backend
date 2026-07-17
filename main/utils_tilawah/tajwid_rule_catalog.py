from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple


SUPPORTED_LEVELS: Tuple[str, ...] = (
    "basic",
    "intermediate",
    "expert",
)

ADVANCED_LEVELS: Tuple[str, ...] = (
    "intermediate",
    "expert",
)

EXPERT_ONLY_LEVELS: Tuple[str, ...] = ("expert",)


class TajwidDisplayGroup(str, Enum):
    """Kelompok visual yang digunakan frontend untuk pewarnaan."""

    REGULAR = "regular"
    NUN_TANWIN = "nun_tanwin"
    MIM_SAKINAH = "mim_sakinah"
    MAD = "mad"
    QALQALAH = "qalqalah"
    GHUNNAH = "ghunnah"
    ALIF_LAM = "alif_lam"
    IDGHAM = "idgham"
    TAFKHIM_TARQIQ = "tafkhim_tarqiq"
    WAQF = "waqf"


class TajwidAppliesWhen(str, Enum):
    """
    Kondisi default berlakunya suatu hukum.

    CONTEXTUAL berarti generator anotasi wajib menentukan kondisi aktual
    berdasarkan posisi hukum pada ayat, misalnya hukum nun mati yang dapat
    terjadi di dalam kata atau pada batas dua kata.
    """

    WASL = "wasl"
    WAQF = "waqf"
    BOTH = "both"
    CONTEXTUAL = "contextual"


class TajwidAssessmentFamily(str, Enum):
    """Jenis bukti akustik utama yang kelak perlu diukur."""

    ARTICULATION = "articulation"
    ASSIMILATION = "assimilation"
    NASALIZATION = "nasalization"
    DURATION = "duration"
    RELEASE = "release"
    RESONANCE = "resonance"
    PAUSE = "pause"
    RENDER_ONLY = "render_only"


# Warna dibuat per kelompok, bukan satu warna unik untuk setiap rule.
# Tujuannya agar UI tetap mudah dipelajari dan tidak memiliki terlalu banyak
# warna yang sulit dibedakan. Semua warna cukup gelap untuk background terang.
TAJWID_COLOR_PALETTE: Mapping[TajwidDisplayGroup, str] = MappingProxyType(
    {
        TajwidDisplayGroup.REGULAR: "0xFF30343B",
        TajwidDisplayGroup.NUN_TANWIN: "0xFF821735",
        TajwidDisplayGroup.MIM_SAKINAH: "0xFF6D28D9",
        TajwidDisplayGroup.MAD: "0xFF256E99",
        TajwidDisplayGroup.QALQALAH: "0xFFB54708",
        TajwidDisplayGroup.GHUNNAH: "0xFF167B60",
        TajwidDisplayGroup.ALIF_LAM: "0xFF79520D",
        TajwidDisplayGroup.IDGHAM: "0xFF4F46A5",
        TajwidDisplayGroup.TAFKHIM_TARQIQ: "0xFF0F766E",
        TajwidDisplayGroup.WAQF: "0xFF9F1239",
    }
)


_COLOR_PATTERN = re.compile(r"^0xFF[0-9A-F]{6}$")
_CODE_PATTERN = re.compile(r"^[a-z0-9_]+$")


@dataclass(frozen=True, slots=True)
class TajwidRuleDefinition:
    """
    Definisi stabil satu hukum tajwid.

    `priority` menggunakan angka lebih kecil sebagai prioritas visual lebih
    tinggi. Priority digunakan ketika dua anotasi menutupi grapheme yang sama.
    Seluruh hukum tetap dapat disimpan, tetapi serializer memilih hukum dengan
    priority tertinggi sebagai warna utama.
    """

    code: str
    name: str
    display_group: TajwidDisplayGroup
    description: str
    priority: int
    default_applies_when: TajwidAppliesWhen
    assessment_family: TajwidAssessmentFamily
    supported_levels: Tuple[str, ...] = SUPPORTED_LEVELS
    expected_features: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not _CODE_PATTERN.fullmatch(self.code):
            raise ValueError(
                f"Invalid tajwid rule code '{self.code}'. "
                "Gunakan huruf kecil, angka, dan underscore."
            )

        if not self.name.strip():
            raise ValueError(f"Rule '{self.code}' harus memiliki name.")

        if not self.description.strip():
            raise ValueError(f"Rule '{self.code}' harus memiliki description.")

        if self.priority < 1:
            raise ValueError(
                f"Rule '{self.code}' harus memiliki priority minimal 1."
            )

        invalid_levels = set(self.supported_levels) - set(SUPPORTED_LEVELS)
        if invalid_levels:
            raise ValueError(
                f"Rule '{self.code}' memiliki level tidak valid: "
                f"{sorted(invalid_levels)}"
            )

        color = TAJWID_COLOR_PALETTE[self.display_group]
        if not _COLOR_PATTERN.fullmatch(color):
            raise ValueError(
                f"Warna untuk group '{self.display_group.value}' tidak valid: "
                f"{color}"
            )

        # Cegah expected_features berubah tanpa sengaja setelah startup.
        object.__setattr__(
            self,
            "expected_features",
            MappingProxyType(dict(self.expected_features)),
        )

    @property
    def color(self) -> str:
        return TAJWID_COLOR_PALETTE[self.display_group]

    def to_dict(self) -> Dict[str, Any]:
        """Representasi serializable untuk seed/model/database."""

        return {
            "code": self.code,
            "name": self.name,
            "display_group": self.display_group.value,
            "description": self.description,
            "color": self.color,
            "priority": self.priority,
            "default_applies_when": self.default_applies_when.value,
            "assessment_family": self.assessment_family.value,
            "supported_levels": list(self.supported_levels),
            "expected_features": dict(self.expected_features),
        }

    def to_frontend_segment(self, arabic: str) -> Dict[str, str]:
        """
        Bentuk dasar segment sesuai kontrak frontend.

        `rule_name` sengaja memakai display_group agar warna dan legenda UI
        stabil. Nama hukum spesifik tetap tersedia melalui `name` di katalog
        dan kelak dapat ditambahkan sebagai field opsional tanpa mengubah group.
        """

        return {
            "rule_name": self.display_group.value,
            "color": self.color,
            "rule_description": self.description,
            "arabic": arabic,
        }


def _rule(
    *,
    code: str,
    name: str,
    display_group: TajwidDisplayGroup,
    description: str,
    priority: int,
    default_applies_when: TajwidAppliesWhen,
    assessment_family: TajwidAssessmentFamily,
    supported_levels: Tuple[str, ...] = SUPPORTED_LEVELS,
    expected_features: Optional[Mapping[str, Any]] = None,
) -> TajwidRuleDefinition:
    return TajwidRuleDefinition(
        code=code,
        name=name,
        display_group=display_group,
        description=description,
        priority=priority,
        default_applies_when=default_applies_when,
        assessment_family=assessment_family,
        supported_levels=supported_levels,
        expected_features=expected_features or {},
    )


_RULES = (
    # ------------------------------------------------------------------
    # Nun mati dan tanwin
    # ------------------------------------------------------------------
    _rule(
        code="izhar_halqi",
        name="Izhar Halqi",
        display_group=TajwidDisplayGroup.NUN_TANWIN,
        description=(
            "Nun mati atau tanwin bertemu huruf halqi dan dibaca jelas "
            "tanpa dilebur."
        ),
        priority=42,
        default_applies_when=TajwidAppliesWhen.CONTEXTUAL,
        assessment_family=TajwidAssessmentFamily.ARTICULATION,
    ),
    _rule(
        code="idgham_bighunnah",
        name="Idgham Bighunnah",
        display_group=TajwidDisplayGroup.IDGHAM,
        description=(
            "Nun mati atau tanwin dilebur ke huruf berikutnya dengan "
            "dengung sekitar 2 harakat."
        ),
        priority=25,
        default_applies_when=TajwidAppliesWhen.WASL,
        assessment_family=TajwidAssessmentFamily.ASSIMILATION,
        expected_features={
            "assimilation": True,
            "nasalization": True,
            "nominal_harakat": 2,
        },
    ),
    _rule(
        code="idgham_bilaghunnah",
        name="Idgham Bilaghunnah",
        display_group=TajwidDisplayGroup.IDGHAM,
        description=(
            "Nun mati atau tanwin dilebur ke huruf lam atau ra tanpa "
            "dengung."
        ),
        priority=24,
        default_applies_when=TajwidAppliesWhen.WASL,
        assessment_family=TajwidAssessmentFamily.ASSIMILATION,
        expected_features={
            "assimilation": True,
            "nasalization": False,
        },
    ),
    _rule(
        code="iqlab",
        name="Iqlab",
        display_group=TajwidDisplayGroup.NUN_TANWIN,
        description=(
            "Nun mati atau tanwin bertemu ba, berubah menjadi bunyi mim "
            "samar dengan dengung sekitar 2 harakat."
        ),
        priority=20,
        default_applies_when=TajwidAppliesWhen.CONTEXTUAL,
        assessment_family=TajwidAssessmentFamily.NASALIZATION,
        expected_features={
            "nasalization": True,
            "nominal_harakat": 2,
            "labial_transition": True,
        },
    ),
    _rule(
        code="ikhfa_haqiqi",
        name="Ikhfa Haqiqi",
        display_group=TajwidDisplayGroup.NUN_TANWIN,
        description=(
            "Nun mati atau tanwin dibaca samar di antara izhar dan idgham "
            "dengan dengung sekitar 2 harakat."
        ),
        priority=28,
        default_applies_when=TajwidAppliesWhen.CONTEXTUAL,
        assessment_family=TajwidAssessmentFamily.NASALIZATION,
        expected_features={
            "nasalization": True,
            "nominal_harakat": 2,
        },
    ),

    # ------------------------------------------------------------------
    # Mim mati
    # ------------------------------------------------------------------
    _rule(
        code="idgham_mimi",
        name="Idgham Mimi",
        display_group=TajwidDisplayGroup.MIM_SAKINAH,
        description=(
            "Mim mati bertemu mim dan dibaca lebur dengan dengung sekitar "
            "2 harakat."
        ),
        priority=26,
        default_applies_when=TajwidAppliesWhen.CONTEXTUAL,
        assessment_family=TajwidAssessmentFamily.NASALIZATION,
        expected_features={
            "assimilation": True,
            "nasalization": True,
            "nominal_harakat": 2,
        },
    ),
    _rule(
        code="ikhfa_syafawi",
        name="Ikhfa Syafawi",
        display_group=TajwidDisplayGroup.MIM_SAKINAH,
        description=(
            "Mim mati bertemu ba dan dibaca samar dengan dengung serta "
            "pertemuan bibir yang ringan."
        ),
        priority=27,
        default_applies_when=TajwidAppliesWhen.CONTEXTUAL,
        assessment_family=TajwidAssessmentFamily.NASALIZATION,
        expected_features={
            "nasalization": True,
            "nominal_harakat": 2,
            "labial_transition": True,
        },
    ),
    _rule(
        code="izhar_syafawi",
        name="Izhar Syafawi",
        display_group=TajwidDisplayGroup.MIM_SAKINAH,
        description=(
            "Mim mati bertemu selain mim dan ba, lalu dibaca jelas."
        ),
        priority=44,
        default_applies_when=TajwidAppliesWhen.CONTEXTUAL,
        assessment_family=TajwidAssessmentFamily.ARTICULATION,
    ),

    # ------------------------------------------------------------------
    # Qalqalah dan ghunnah
    # ------------------------------------------------------------------
    _rule(
        code="qalqalah_sugra",
        name="Qalqalah Sugra",
        display_group=TajwidDisplayGroup.QALQALAH,
        description=(
            "Huruf qalqalah bersukun asli dibaca dengan pantulan ringan."
        ),
        priority=34,
        default_applies_when=TajwidAppliesWhen.BOTH,
        assessment_family=TajwidAssessmentFamily.RELEASE,
        expected_features={"release_strength": "light"},
    ),
    _rule(
        code="qalqalah_kubra",
        name="Qalqalah Kubra",
        display_group=TajwidDisplayGroup.QALQALAH,
        description=(
            "Huruf qalqalah menjadi sukun karena waqaf dan dibaca dengan "
            "pantulan yang lebih kuat."
        ),
        priority=18,
        default_applies_when=TajwidAppliesWhen.WAQF,
        assessment_family=TajwidAssessmentFamily.RELEASE,
        expected_features={"release_strength": "strong"},
    ),
    _rule(
        code="ghunnah",
        name="Ghunnah Musyaddadah",
        display_group=TajwidDisplayGroup.GHUNNAH,
        description=(
            "Mim atau nun bertasydid dibaca dengan dengung sekitar 2 harakat."
        ),
        priority=30,
        default_applies_when=TajwidAppliesWhen.BOTH,
        assessment_family=TajwidAssessmentFamily.NASALIZATION,
        expected_features={
            "nasalization": True,
            "nominal_harakat": 2,
        },
    ),

    # ------------------------------------------------------------------
    # Alif lam
    # ------------------------------------------------------------------
    _rule(
        code="alif_lam_syamsiah",
        name="Alif Lam Syamsiah",
        display_group=TajwidDisplayGroup.ALIF_LAM,
        description=(
            "Lam ta'rif bertemu huruf syamsiah sehingga lam tidak dibaca "
            "dan huruf sesudahnya ditekan."
        ),
        priority=52,
        default_applies_when=TajwidAppliesWhen.BOTH,
        assessment_family=TajwidAssessmentFamily.ASSIMILATION,
    ),
    _rule(
        code="alif_lam_qamariah",
        name="Alif Lam Qamariah",
        display_group=TajwidDisplayGroup.ALIF_LAM,
        description=(
            "Lam ta'rif bertemu huruf qamariah sehingga lam dibaca jelas."
        ),
        priority=54,
        default_applies_when=TajwidAppliesWhen.BOTH,
        assessment_family=TajwidAssessmentFamily.ARTICULATION,
    ),

    # ------------------------------------------------------------------
    # Mad
    # ------------------------------------------------------------------
    _rule(
        code="mad_asli",
        name="Mad Asli (Thabi'i)",
        display_group=TajwidDisplayGroup.MAD,
        description="Huruf mad dibaca sepanjang 2 harakat.",
        priority=90,
        default_applies_when=TajwidAppliesWhen.BOTH,
        assessment_family=TajwidAssessmentFamily.DURATION,
        expected_features={
            "min_harakat": 2,
            "max_harakat": 2,
            "nominal_harakat": 2,
        },
    ),
    _rule(
        code="mad_wajib_muttasil",
        name="Mad Wajib Muttasil",
        display_group=TajwidDisplayGroup.MAD,
        description=(
            "Huruf mad bertemu hamzah dalam satu kata dan dibaca panjang "
            "4 sampai 5 harakat."
        ),
        priority=14,
        default_applies_when=TajwidAppliesWhen.BOTH,
        assessment_family=TajwidAssessmentFamily.DURATION,
        supported_levels=ADVANCED_LEVELS,
        expected_features={
            "min_harakat": 4,
            "max_harakat": 5,
        },
    ),
    _rule(
        code="mad_jaiz_munfasil",
        name="Mad Jaiz Munfasil",
        display_group=TajwidDisplayGroup.MAD,
        description=(
            "Huruf mad di akhir kata bertemu hamzah pada kata berikutnya; "
            "panjang bacaan mengikuti riwayat dan metode pembelajaran yang "
            "digunakan."
        ),
        priority=16,
        default_applies_when=TajwidAppliesWhen.WASL,
        assessment_family=TajwidAssessmentFamily.DURATION,
        supported_levels=ADVANCED_LEVELS,
        expected_features={
            "min_harakat": 2,
            "max_harakat": 5,
            "requires_recitation_profile": True,
        },
    ),
    _rule(
        code="mad_lazim_mutsaqqal",
        name="Mad Lazim Mutsaqqal",
        display_group=TajwidDisplayGroup.MAD,
        description=(
            "Huruf mad bertemu huruf bertasydid dan dibaca sepanjang "
            "6 harakat."
        ),
        priority=11,
        default_applies_when=TajwidAppliesWhen.BOTH,
        assessment_family=TajwidAssessmentFamily.DURATION,
        supported_levels=ADVANCED_LEVELS,
        expected_features={
            "min_harakat": 6,
            "max_harakat": 6,
            "nominal_harakat": 6,
        },
    ),
    _rule(
        code="mad_lazim_mukhaffaf",
        name="Mad Lazim Mukhaffaf",
        display_group=TajwidDisplayGroup.MAD,
        description=(
            "Huruf mad bertemu sukun asli dan dibaca sepanjang 6 harakat."
        ),
        priority=12,
        default_applies_when=TajwidAppliesWhen.BOTH,
        assessment_family=TajwidAssessmentFamily.DURATION,
        supported_levels=ADVANCED_LEVELS,
        expected_features={
            "min_harakat": 6,
            "max_harakat": 6,
            "nominal_harakat": 6,
        },
    ),
    _rule(
        code="mad_aridh_lissukun",
        name="Mad Aridh Lissukun",
        display_group=TajwidDisplayGroup.MAD,
        description=(
            "Huruf mad diikuti huruf yang menjadi sukun karena waqaf dan "
            "dapat dibaca 2, 4, atau 6 harakat."
        ),
        priority=13,
        default_applies_when=TajwidAppliesWhen.WAQF,
        assessment_family=TajwidAssessmentFamily.DURATION,
        supported_levels=ADVANCED_LEVELS,
        expected_features={
            "allowed_harakat": [2, 4, 6],
        },
    ),
    _rule(
        code="mad_lin",
        name="Mad Lin",
        display_group=TajwidDisplayGroup.MAD,
        description=(
            "Waw atau ya sukun yang didahului fathah dibaca lunak dan dapat "
            "dipanjangkan ketika waqaf."
        ),
        priority=15,
        default_applies_when=TajwidAppliesWhen.WAQF,
        assessment_family=TajwidAssessmentFamily.DURATION,
        supported_levels=ADVANCED_LEVELS,
        expected_features={
            "allowed_harakat": [2, 4, 6],
        },
    ),
    _rule(
        code="mad_iwad",
        name="Mad Iwad",
        display_group=TajwidDisplayGroup.MAD,
        description=(
            "Tanwin fathah pada akhir bacaan ketika waqaf diganti dengan "
            "panjang 2 harakat."
        ),
        priority=10,
        default_applies_when=TajwidAppliesWhen.WAQF,
        assessment_family=TajwidAssessmentFamily.DURATION,
        supported_levels=ADVANCED_LEVELS,
        expected_features={
            "min_harakat": 2,
            "max_harakat": 2,
            "nominal_harakat": 2,
        },
    ),
    _rule(
        code="mad_silah_qasirah",
        name="Mad Silah Qasirah",
        display_group=TajwidDisplayGroup.MAD,
        description=(
            "Ha dhamir di antara dua huruf hidup dan tidak diikuti hamzah "
            "dibaca panjang 2 harakat saat wasl."
        ),
        priority=17,
        default_applies_when=TajwidAppliesWhen.WASL,
        assessment_family=TajwidAssessmentFamily.DURATION,
        supported_levels=ADVANCED_LEVELS,
        expected_features={
            "min_harakat": 2,
            "max_harakat": 2,
            "nominal_harakat": 2,
        },
    ),
    _rule(
        code="mad_silah_thawilah",
        name="Mad Silah Thawilah",
        display_group=TajwidDisplayGroup.MAD,
        description=(
            "Ha dhamir bertemu hamzah pada kata berikutnya dan dibaca "
            "panjang saat wasl."
        ),
        priority=12,
        default_applies_when=TajwidAppliesWhen.WASL,
        assessment_family=TajwidAssessmentFamily.DURATION,
        supported_levels=ADVANCED_LEVELS,
        expected_features={
            "min_harakat": 4,
            "max_harakat": 5,
            "requires_recitation_profile": True,
        },
    ),

    # ------------------------------------------------------------------
    # Idgham selain nun mati/tanwin
    # ------------------------------------------------------------------
    _rule(
        code="idgham_mutamatsilain",
        name="Idgham Mutamatsilain",
        display_group=TajwidDisplayGroup.IDGHAM,
        description=(
            "Dua huruf yang sama bertemu, huruf pertama mati dan dilebur "
            "ke huruf kedua."
        ),
        priority=32,
        default_applies_when=TajwidAppliesWhen.CONTEXTUAL,
        assessment_family=TajwidAssessmentFamily.ASSIMILATION,
        supported_levels=ADVANCED_LEVELS,
        expected_features={"assimilation": True},
    ),
    _rule(
        code="idgham_mutajanisain",
        name="Idgham Mutajanisain",
        display_group=TajwidDisplayGroup.IDGHAM,
        description=(
            "Dua huruf yang makhrajnya sama atau sangat berdekatan tetapi "
            "sifatnya berbeda dibaca dengan peleburan yang sesuai."
        ),
        priority=33,
        default_applies_when=TajwidAppliesWhen.CONTEXTUAL,
        assessment_family=TajwidAssessmentFamily.ASSIMILATION,
        supported_levels=ADVANCED_LEVELS,
        expected_features={"assimilation": True},
    ),
    _rule(
        code="idgham_mutaqaribain",
        name="Idgham Mutaqaribain",
        display_group=TajwidDisplayGroup.IDGHAM,
        description=(
            "Dua huruf yang makhraj atau sifatnya berdekatan dibaca dengan "
            "peleburan yang sesuai."
        ),
        priority=35,
        default_applies_when=TajwidAppliesWhen.CONTEXTUAL,
        assessment_family=TajwidAssessmentFamily.ASSIMILATION,
        supported_levels=ADVANCED_LEVELS,
        expected_features={"assimilation": True},
    ),

    # ------------------------------------------------------------------
    # Tafkhim dan tarqiq
    # ------------------------------------------------------------------
    _rule(
        code="tafkhim_ra",
        name="Tafkhim Ra",
        display_group=TajwidDisplayGroup.TAFKHIM_TARQIQ,
        description="Huruf ra dibaca tebal sesuai konteks harakatnya.",
        priority=48,
        default_applies_when=TajwidAppliesWhen.CONTEXTUAL,
        assessment_family=TajwidAssessmentFamily.RESONANCE,
        supported_levels=ADVANCED_LEVELS,
        expected_features={"resonance": "emphatic"},
    ),
    _rule(
        code="tarqiq_ra",
        name="Tarqiq Ra",
        display_group=TajwidDisplayGroup.TAFKHIM_TARQIQ,
        description="Huruf ra dibaca tipis sesuai konteks harakatnya.",
        priority=48,
        default_applies_when=TajwidAppliesWhen.CONTEXTUAL,
        assessment_family=TajwidAssessmentFamily.RESONANCE,
        supported_levels=ADVANCED_LEVELS,
        expected_features={"resonance": "light"},
    ),
    _rule(
        code="tafkhim_lam_jalalah",
        name="Tafkhim Lam Jalalah",
        display_group=TajwidDisplayGroup.TAFKHIM_TARQIQ,
        description=(
            "Lam pada lafaz Allah dibaca tebal ketika didahului fathah "
            "atau dammah."
        ),
        priority=46,
        default_applies_when=TajwidAppliesWhen.CONTEXTUAL,
        assessment_family=TajwidAssessmentFamily.RESONANCE,
        supported_levels=ADVANCED_LEVELS,
        expected_features={"resonance": "emphatic"},
    ),
    _rule(
        code="tarqiq_lam_jalalah",
        name="Tarqiq Lam Jalalah",
        display_group=TajwidDisplayGroup.TAFKHIM_TARQIQ,
        description=(
            "Lam pada lafaz Allah dibaca tipis ketika didahului kasrah."
        ),
        priority=46,
        default_applies_when=TajwidAppliesWhen.CONTEXTUAL,
        assessment_family=TajwidAssessmentFamily.RESONANCE,
        supported_levels=ADVANCED_LEVELS,
        expected_features={"resonance": "light"},
    ),

    # ------------------------------------------------------------------
    # Waqaf khusus
    # ------------------------------------------------------------------
    _rule(
        code="saktah",
        name="Saktah",
        display_group=TajwidDisplayGroup.WAQF,
        description=(
            "Berhenti sangat singkat tanpa mengambil napas, kemudian "
            "melanjutkan bacaan."
        ),
        priority=5,
        default_applies_when=TajwidAppliesWhen.BOTH,
        assessment_family=TajwidAssessmentFamily.PAUSE,
        supported_levels=EXPERT_ONLY_LEVELS,
        expected_features={
            "pause_required": True,
            "breath_allowed": False,
        },
    ),
)


TAJWID_RULE_CATALOG: Mapping[str, TajwidRuleDefinition] = MappingProxyType(
    {rule.code: rule for rule in _RULES}
)


REGULAR_RENDER_RULE: Mapping[str, str] = MappingProxyType(
    {
        "rule_name": TajwidDisplayGroup.REGULAR.value,
        "color": TAJWID_COLOR_PALETTE[TajwidDisplayGroup.REGULAR],
        "rule_description": "",
    }
)


def validate_rule_catalog() -> None:
    """Fail-fast validation untuk mencegah katalog ambigu atau tidak lengkap."""

    if len(TAJWID_RULE_CATALOG) != len(_RULES):
        seen = set()
        duplicates = set()
        for rule in _RULES:
            if rule.code in seen:
                duplicates.add(rule.code)
            seen.add(rule.code)
        raise ValueError(
            "Duplicate tajwid rule code ditemukan: "
            f"{sorted(duplicates)}"
        )

    for code, rule in TAJWID_RULE_CATALOG.items():
        if code != rule.code:
            raise ValueError(
                f"Catalog key '{code}' tidak sama dengan rule.code "
                f"'{rule.code}'."
            )


def assert_rule_codes_registered(rule_codes: Iterable[str]) -> None:
    """
    Pastikan semua rule code yang dipancarkan Tajwid Engine terdaftar.

    Fungsi ini akan digunakan oleh test dan management command pada tahap
    berikutnya agar penambahan rule baru tidak diam-diam kehilangan warna,
    deskripsi, atau metadata assessment.
    """

    requested = {code for code in rule_codes if code}
    unknown = requested - set(TAJWID_RULE_CATALOG)
    if unknown:
        raise KeyError(
            "Rule code belum terdaftar di tajwid_rule_catalog.py: "
            f"{sorted(unknown)}"
        )


def get_rule_definition(code: str) -> TajwidRuleDefinition:
    """Ambil definisi rule atau raise KeyError dengan pesan yang jelas."""

    try:
        return TAJWID_RULE_CATALOG[code]
    except KeyError as exc:
        raise KeyError(
            f"Tajwid rule '{code}' belum terdaftar di catalog."
        ) from exc


def get_rule_definition_or_none(
    code: str,
) -> Optional[TajwidRuleDefinition]:
    return TAJWID_RULE_CATALOG.get(code)


def iter_rule_definitions() -> Tuple[TajwidRuleDefinition, ...]:
    """Return rule terurut berdasarkan priority lalu code."""

    return tuple(
        sorted(
            TAJWID_RULE_CATALOG.values(),
            key=lambda item: (item.priority, item.code),
        )
    )


def catalog_as_dict() -> Dict[str, Dict[str, Any]]:
    """Return copy serializable; aman dipakai management command."""

    return {
        code: rule.to_dict()
        for code, rule in TAJWID_RULE_CATALOG.items()
    }


def build_regular_frontend_segment(arabic: str) -> Dict[str, str]:
    """Bentuk segment regular tanpa menyimpannya sebagai anotasi database."""

    return {
        **dict(REGULAR_RENDER_RULE),
        "arabic": arabic,
    }


# Jalankan validasi saat module pertama kali di-import.
validate_rule_catalog()
