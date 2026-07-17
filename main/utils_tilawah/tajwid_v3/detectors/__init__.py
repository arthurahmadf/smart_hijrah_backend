from .advanced_idgham import (
    AdvancedIdghamDetector,
    SUPPORTED_RULE_CODES as ADVANCED_IDGHAM_SUPPORTED_RULE_CODES,
)
from .alif_lam import (
    AlifLamDetector,
    SUPPORTED_RULE_CODES as ALIF_LAM_SUPPORTED_RULE_CODES,
)
from .advanced_mad import (
    AdvancedMadDetector,
    SUPPORTED_RULE_CODES as ADVANCED_MAD_SUPPORTED_RULE_CODES,
)
from .base import DetectorIssue, DetectorOutput, TajwidDetector
from .ghunnah import (
    GhunnahMushaddadahDetector,
    SUPPORTED_RULE_CODES as GHUNNAH_SUPPORTED_RULE_CODES,
)
from .mad import (
    MadDetector,
    SUPPORTED_RULE_CODES as MAD_SUPPORTED_RULE_CODES,
)
from .mim_sakinah import (
    MimSakinahDetector,
    SUPPORTED_RULE_CODES as MIM_SAKINAH_SUPPORTED_RULE_CODES,
)
from .orthographic_waqf import (
    OrthographicWaqfDetector,
    SUPPORTED_RULE_CODES as ORTHOGRAPHIC_WAQF_SUPPORTED_RULE_CODES,
)
from .ra import (
    RaDetector,
    SUPPORTED_RULE_CODES as RA_SUPPORTED_RULE_CODES,
)
from .qalqalah import (
    QalqalahDetector,
    SUPPORTED_RULE_CODES as QALQALAH_SUPPORTED_RULE_CODES,
)
from .nun_tanwin import (
    NunTanwinDetector,
    SUPPORTED_RULE_CODES as NUN_TANWIN_SUPPORTED_RULE_CODES,
)

# Backward-compatible alias retained for Stage 5D callers.
SUPPORTED_RULE_CODES = NUN_TANWIN_SUPPORTED_RULE_CODES

__all__ = [
    "ADVANCED_IDGHAM_SUPPORTED_RULE_CODES",
    "ADVANCED_MAD_SUPPORTED_RULE_CODES",
    "AdvancedIdghamDetector",
    "ALIF_LAM_SUPPORTED_RULE_CODES",
    "AlifLamDetector",
    "AdvancedMadDetector",
    "DetectorIssue",
    "DetectorOutput",
    "GHUNNAH_SUPPORTED_RULE_CODES",
    "GhunnahMushaddadahDetector",
    "MAD_SUPPORTED_RULE_CODES",
    "MadDetector",
    "MIM_SAKINAH_SUPPORTED_RULE_CODES",
    "MimSakinahDetector",
    "NUN_TANWIN_SUPPORTED_RULE_CODES",
    "ORTHOGRAPHIC_WAQF_SUPPORTED_RULE_CODES",
    "OrthographicWaqfDetector",
    "QALQALAH_SUPPORTED_RULE_CODES",
    "RA_SUPPORTED_RULE_CODES",
    "RaDetector",
    "QalqalahDetector",
    "NunTanwinDetector",
    "SUPPORTED_RULE_CODES",
    "TajwidDetector",
]
