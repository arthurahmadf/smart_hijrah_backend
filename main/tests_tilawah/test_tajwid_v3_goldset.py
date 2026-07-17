from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from main.utils_tilawah.tajwid_v3.gold_loader import load_gold_dataset
from main.utils_tilawah.tajwid_v3.gold_schema import (
    CaseKind,
    ReviewStatus,
    default_gold_dataset_path,
)
from main.utils_tilawah.tajwid_v3.gold_validation import validate_gold_dataset
from main.utils_tilawah.tajwid_v3.rule_specs import RULE_SPECS
from main.utils_tilawah.tajwid_v3.specification import DetectionMaturity


class TajwidV3GoldsetTests(SimpleTestCase):
    databases = set()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dataset_path = default_gold_dataset_path(Path(settings.BASE_DIR))
        cls.dataset = load_gold_dataset(cls.dataset_path)
        cls.report = validate_gold_dataset(cls.dataset)

    def test_bootstrap_dataset_is_structurally_valid(self):
        self.assertEqual(self.report.error_count, 0)
        self.assertTrue(self.report.structural_ready)
        self.assertTrue(self.report.detector_development_ready)

    def test_bootstrap_dataset_is_not_claimed_as_production_gold(self):
        self.assertFalse(self.report.production_ready)
        self.assertEqual(self.report.expert_verified_cases, 0)
        self.assertEqual(self.dataset.status, "bootstrap_provisional")

    def test_all_rule_specs_have_minimum_development_coverage(self):
        coverage = {item.rule_code: item for item in self.report.coverage}
        self.assertEqual(set(coverage), set(RULE_SPECS))
        for rule_code, item in coverage.items():
            self.assertTrue(item.structural_gate_passed, rule_code)

    def test_core_rules_have_positive_and_negative_cases(self):
        coverage = {item.rule_code: item for item in self.report.coverage}
        for code, rule in RULE_SPECS.items():
            if rule.detection_maturity != DetectionMaturity.CORE_DETERMINISTIC:
                continue
            self.assertGreaterEqual(coverage[code].positive, 1, code)
            self.assertGreaterEqual(coverage[code].negative, 1, code)

    def test_exception_rules_have_positive_negative_and_exception_cases(self):
        coverage = {item.rule_code: item for item in self.report.coverage}
        for code, rule in RULE_SPECS.items():
            if (
                rule.detection_maturity
                != DetectionMaturity.DETERMINISTIC_WITH_EXCEPTIONS
            ):
                continue
            self.assertGreaterEqual(coverage[code].positive, 1, code)
            self.assertGreaterEqual(coverage[code].negative, 1, code)
            self.assertGreaterEqual(coverage[code].exception, 1, code)

    def test_complex_rules_are_explicitly_queued_for_expert_review(self):
        candidate_rules = {
            case.rule_under_test
            for case in self.dataset.cases
            if case.kind == CaseKind.CANDIDATE
            and case.review_status == ReviewStatus.EXPERT_REQUIRED
        }
        expected = {
            code
            for code, rule in RULE_SPECS.items()
            if rule.detection_maturity
            in {
                DetectionMaturity.EXPERT_GOLDSET_REQUIRED,
                DetectionMaturity.REFERENCE_ASSISTED,
            }
        }
        self.assertEqual(candidate_rules, expected)

    def test_external_quran_foundation_reference_case_is_present(self):
        cases = {case.case_id: case for case in self.dataset.cases}
        reference = cases["reference_quran_foundation_1_1_001"]
        self.assertEqual(reference.review_status, ReviewStatus.REFERENCE_CHECKED)
        self.assertIn("QURAN_FOUNDATION_TAJWEED_V4", reference.source_ids)
        self.assertEqual(reference.verse_key, "1:1")

    def test_all_expected_anchors_resolve_on_grapheme_boundaries(self):
        # validate_gold_dataset resolves every trigger/context/display span.
        invalid_anchor_issues = [
            issue
            for issue in self.report.issues
            if issue.issue_type == "invalid_anchor"
        ]
        self.assertEqual(invalid_anchor_issues, [])
