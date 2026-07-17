from __future__ import annotations

import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Dict, Mapping, Tuple

from .rule_specs import RULE_SPECS
from .specification import DisplayGroup


DISPLAY_SCHEMA_VERSION = "3.0.0-alpha.1"
_COLOR_PATTERN = re.compile(r"^0xFF[0-9A-F]{6}$")


# Palette sengaja terbatas per kelompok agar legenda mudah dipelajari dan
# tetap serasi dengan warna utama Smart Hijrah.
DISPLAY_COLOR_PALETTE: Mapping[DisplayGroup, str] = MappingProxyType(
    {
        DisplayGroup.REGULAR: "0xFF30343B",
        DisplayGroup.NUN_TANWIN: "0xFF821735",
        DisplayGroup.MIM_SAKINAH: "0xFF6D28D9",
        DisplayGroup.GHUNNAH: "0xFF167B60",
        DisplayGroup.QALQALAH: "0xFFB54708",
        DisplayGroup.ALIF_LAM: "0xFF79520D",
        DisplayGroup.TAFKHIM_TARQIQ: "0xFF0F766E",
        DisplayGroup.MADD: "0xFF256E99",
        DisplayGroup.IDGHAM: "0xFF4F46A5",
        DisplayGroup.ORTHOGRAPHIC: "0xFF64748B",
        DisplayGroup.WAQF: "0xFF9F1239",
    }
)


# Angka lebih kecil menang sebagai warna utama ketika beberapa hukum menutup
# grapheme yang sama. Semua hukum tetap tersedia sebagai secondary rule.
_PRIORITY_OVERRIDES: Mapping[str, int] = MappingProxyType(
    {
        "saktah_wajibah": 5,
        "saktah_jaizah": 6,
        "silent_letter": 8,
        "mad_farq": 10,
        "mad_lazim_harfi_muthaqqal": 11,
        "mad_lazim_harfi_mukhaffaf": 12,
        "mad_lazim_kalimi_muthaqqal": 13,
        "mad_lazim_kalimi_mukhaffaf": 14,
        "mad_ayn_muqattaah": 15,
        "mad_wajib_muttasil": 16,
        "mad_jaiz_munfasil": 17,
        "mad_silah_tawilah": 18,
        "mad_silah_qasirah": 19,
        "mad_arid_lissukun": 20,
        "mad_lin": 21,
        "mad_iwad": 22,
        "mad_tamkin": 23,
        "idgham_mutajanisain": 25,
        "idgham_mutaqaribain": 26,
        "idgham_mutamathilain": 27,
        "idgham_bighunnah": 28,
        "idgham_bilaghunnah": 29,
        "idgham_mimi": 30,
        "iqlab": 31,
        "ikhfa_haqiqi": 32,
        "ikhfa_shafawi": 33,
        "ghunnah_mushaddadah": 34,
        "qalqalah_akbar": 35,
        "qalqalah_kubra": 36,
        "qalqalah_sughra": 37,
        "ra_both_permitted": 40,
        "ra_tafkhim": 41,
        "ra_tarqiq": 42,
        "lam_jalalah_tafkhim": 43,
        "lam_jalalah_tarqiq": 44,
        "alif_lam_shamsiyyah": 50,
        "alif_lam_qamariyyah": 51,
        "izhar_mutlaq": 55,
        "izhar_halqi": 56,
        "izhar_shafawi": 57,
        "mad_badl": 60,
        "mad_harfi_tabii": 61,
        "mad_tabii": 70,
        "hamzat_wasl": 80,
    }
)

_DEFAULT_GROUP_PRIORITY: Mapping[DisplayGroup, int] = MappingProxyType(
    {
        DisplayGroup.WAQF: 10,
        DisplayGroup.ORTHOGRAPHIC: 20,
        DisplayGroup.IDGHAM: 30,
        DisplayGroup.GHUNNAH: 35,
        DisplayGroup.QALQALAH: 40,
        DisplayGroup.TAFKHIM_TARQIQ: 45,
        DisplayGroup.ALIF_LAM: 50,
        DisplayGroup.NUN_TANWIN: 55,
        DisplayGroup.MIM_SAKINAH: 56,
        DisplayGroup.MADD: 70,
        DisplayGroup.REGULAR: 999,
    }
)


@dataclass(frozen=True, slots=True)
class RuleDisplayDefinition:
    rule_code: str
    rule_title: str
    rule_name: str
    display_group: DisplayGroup
    color: str
    description: str
    priority: int

    def to_frontend_dict(self, arabic: str) -> Dict[str, str]:
        return {
            "rule_name": self.rule_name,
            "color": self.color,
            "rule_description": self.description,
            "arabic": arabic,
        }


REGULAR_DISPLAY = RuleDisplayDefinition(
    rule_code="regular",
    rule_title="Regular",
    rule_name="regular",
    display_group=DisplayGroup.REGULAR,
    color=DISPLAY_COLOR_PALETTE[DisplayGroup.REGULAR],
    description="",
    priority=999,
)


def _build_display_catalog() -> Mapping[str, RuleDisplayDefinition]:
    catalog = {}
    for code, spec in RULE_SPECS.items():
        color = DISPLAY_COLOR_PALETTE[spec.display_group]
        priority = _PRIORITY_OVERRIDES.get(
            code,
            _DEFAULT_GROUP_PRIORITY[spec.display_group],
        )
        catalog[code] = RuleDisplayDefinition(
            rule_code=code,
            rule_title=spec.name,
            rule_name=spec.display_group.value,
            display_group=spec.display_group,
            color=color,
            description=spec.description,
            priority=priority,
        )
    return MappingProxyType(catalog)


RULE_DISPLAY_CATALOG: Mapping[str, RuleDisplayDefinition] = _build_display_catalog()


def validate_display_catalog() -> Tuple[str, ...]:
    issues = []
    missing = set(RULE_SPECS) - set(RULE_DISPLAY_CATALOG)
    extra = set(RULE_DISPLAY_CATALOG) - set(RULE_SPECS)
    if missing:
        issues.append(f"missing_rule_display:{','.join(sorted(missing))}")
    if extra:
        issues.append(f"unknown_rule_display:{','.join(sorted(extra))}")
    for group, color in DISPLAY_COLOR_PALETTE.items():
        if not _COLOR_PATTERN.fullmatch(color):
            issues.append(f"invalid_color:{group.value}:{color}")
    for code, item in RULE_DISPLAY_CATALOG.items():
        if item.priority < 1:
            issues.append(f"invalid_priority:{code}")
        if item.rule_code != code:
            issues.append(f"catalog_key_mismatch:{code}")
    return tuple(issues)


_DISPLAY_ISSUES = validate_display_catalog()
if _DISPLAY_ISSUES:
    raise RuntimeError(f"Tajwid display catalog invalid: {_DISPLAY_ISSUES}")


def get_rule_display(rule_code: str) -> RuleDisplayDefinition:
    if rule_code == "regular":
        return REGULAR_DISPLAY
    try:
        return RULE_DISPLAY_CATALOG[rule_code]
    except KeyError as exc:
        raise KeyError(f"Rule display '{rule_code}' tidak terdaftar.") from exc


def display_priority(rule_code: str) -> int:
    return get_rule_display(rule_code).priority
