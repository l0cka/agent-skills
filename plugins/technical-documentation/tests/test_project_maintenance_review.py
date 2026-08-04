#!/usr/bin/env python3
"""Contract tests for the project maintenance review skill."""

from __future__ import annotations

from pathlib import Path
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PLUGIN_ROOT / "skills" / "review-project-maintenance"
SKILL_TEXT = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
RUBRIC_TEXT = (SKILL_ROOT / "references" / "review-rubric.md").read_text(
    encoding="utf-8"
)


class ProjectMaintenanceReviewContractTest(unittest.TestCase):
    def test_review_and_apply_are_separate_phases(self):
        self.assertIn("REVIEWED_AWAITING_APPROVAL", SKILL_TEXT)
        self.assertIn("Do not include an edit in the same turn as this gate", SKILL_TEXT)
        self.assertIn("APPLIED_VERIFIED", SKILL_TEXT)

    def test_explicit_item_approval_is_required(self):
        self.assertIn("explicit approval of `ALL`", SKILL_TEXT)
        self.assertIn("named proposal IDs", SKILL_TEXT)
        self.assertIn("Do not quietly expand the set", SKILL_TEXT)
        self.assertIn("supplemental approval", SKILL_TEXT)

    def test_review_stays_read_only(self):
        normalized = " ".join(SKILL_TEXT.split())
        self.assertIn("Keep the review read-only", normalized)
        self.assertIn("do not modify tracked files or external state", normalized)

    def test_findings_require_evidence_not_style_preference(self):
        self.assertIn("Include a finding only when all four statements are true", RUBRIC_TEXT)
        self.assertIn("personal style", RUBRIC_TEXT)
        self.assertIn("Search results alone do not prove dead code", RUBRIC_TEXT)
        self.assertIn("newer dependency version alone", RUBRIC_TEXT)

    def test_skill_has_ui_metadata(self):
        metadata = SKILL_ROOT / "agents" / "openai.yaml"
        self.assertTrue(metadata.is_file())
        self.assertIn("$review-project-maintenance", metadata.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
