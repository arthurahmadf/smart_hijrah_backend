from django.test import SimpleTestCase

from main.utils_tilawah.tajwid_v3.rule_specs import (
    EXPECTED_RULE_CODES,
    RULE_SPECS,
)
from main.utils_tilawah.tajwid_v3.specification import (
    AcousticAssessment,
    DEFAULT_RECITATION_PROFILE_ID,
    DetectionMaturity,
    DisplayGroup,
    HAFS_ASIM_SHATIBIYYAH_PROFILE,
    ReadingMode,
    SOURCE_REFERENCES,
    SPECIFICATION_VERSION,
    VerificationState,
    get_recitation_profile,
    validate_rule_specs,
)


class TajwidV3SpecificationTests(SimpleTestCase):
    def test_specification_version_is_explicit(self):
        self.assertEqual(SPECIFICATION_VERSION, "3.0.0-alpha.1")

    def test_rule_taxonomy_is_complete_and_unique(self):
        self.assertEqual(set(RULE_SPECS), set(EXPECTED_RULE_CODES))
        self.assertEqual(len(RULE_SPECS), 44)
        validate_rule_specs(RULE_SPECS)

    def test_regular_is_not_a_persisted_rule(self):
        self.assertNotIn("regular", RULE_SPECS)
        self.assertFalse(
            any(rule.display_group == DisplayGroup.REGULAR for rule in RULE_SPECS.values())
        )

    def test_every_rule_has_a_known_source(self):
        for rule in RULE_SPECS.values():
            self.assertTrue(rule.source_ids, rule.code)
            for source_id in rule.source_ids:
                self.assertIn(source_id, SOURCE_REFERENCES, rule.code)

    def test_complex_rules_are_not_marked_as_core(self):
        complex_codes = {
            "ra_tafkhim",
            "ra_tarqiq",
            "ra_both_permitted",
            "mad_silah_qasirah",
            "mad_silah_tawilah",
            "mad_tamkin",
            "idgham_mutajanisain",
            "idgham_mutaqaribain",
        }
        for code in complex_codes:
            self.assertNotEqual(
                RULE_SPECS[code].detection_maturity,
                DetectionMaturity.CORE_DETERMINISTIC,
                code,
            )

    def test_render_only_rules_are_not_acoustically_scored(self):
        self.assertEqual(
            RULE_SPECS["hamzat_wasl"].acoustic_assessment,
            AcousticAssessment.RENDER_ONLY,
        )
        self.assertEqual(
            RULE_SPECS["silent_letter"].acoustic_assessment,
            AcousticAssessment.RENDER_ONLY,
        )

    def test_default_recitation_profile_is_hafs_shatibiyyah(self):
        profile = get_recitation_profile(DEFAULT_RECITATION_PROFILE_ID)
        self.assertEqual(profile, HAFS_ASIM_SHATIBIYYAH_PROFILE)
        self.assertEqual(profile.qiraah, "Asim")
        self.assertEqual(profile.riwayah, "Hafs")
        self.assertEqual(profile.tariq, "al-Shatibiyyah")
        self.assertEqual(profile.default_reading_mode, ReadingMode.AYAH_STOP)

    def test_profile_madd_settings_do_not_mix_qasr_munfasil(self):
        profile = HAFS_ASIM_SHATIBIYYAH_PROFILE
        muttasil = profile.madd_settings["mad_wajib_muttasil"]
        munfasil = profile.madd_settings["mad_jaiz_munfasil"]
        self.assertEqual(muttasil.allowed_harakat, (4, 5))
        self.assertEqual(munfasil.allowed_harakat, (4, 5))
        self.assertEqual(muttasil.default_harakat, 4)
        self.assertEqual(munfasil.default_harakat, 4)
        self.assertEqual(muttasil.consistency_group, munfasil.consistency_group)

    def test_profile_has_four_mandatory_saktah_locations(self):
        profile = HAFS_ASIM_SHATIBIYYAH_PROFILE
        self.assertEqual(len(profile.mandatory_saktah), 4)
        locations = {
            (item.start_verse_key, item.end_verse_key)
            for item in profile.mandatory_saktah
        }
        self.assertEqual(
            locations,
            {
                ("18:1", "18:2"),
                ("36:52", "36:52"),
                ("75:27", "75:27"),
                ("83:14", "83:14"),
            },
        )

    def test_all_rules_are_provisional_until_independent_review(self):
        for rule in RULE_SPECS.values():
            self.assertIn(
                rule.verification_state,
                {
                    VerificationState.PROVISIONAL,
                    VerificationState.REFERENCE_CHECKED,
                    VerificationState.EXPERT_VERIFIED,
                },
            )
        self.assertTrue(
            any(
                rule.verification_state == VerificationState.PROVISIONAL
                for rule in RULE_SPECS.values()
            )
        )
