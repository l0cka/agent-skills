#!/usr/bin/env python3
"""Contract tests for the executive-dysfunction agent skill."""

import json
from pathlib import Path
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
SKILL_ROOT = PLUGIN_ROOT / "skills" / "executive-dysfunction"
SKILL_TEXT = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
EVIDENCE_PATH = SKILL_ROOT / "references" / "evidence-base.md"


class ExecutiveDysfunctionContractTests(unittest.TestCase):
    def assertContainsAll(self, text: str, phrases: tuple[str, ...]) -> None:
        lowered = text.lower()
        for phrase in phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.lower(), lowered)

    def test_skill_has_complete_frontmatter_and_no_placeholders(self):
        self.assertTrue(SKILL_TEXT.startswith("---\n"))
        self.assertIn("name: executive-dysfunction", SKILL_TEXT)
        self.assertRegex(
            SKILL_TEXT,
            r"description: .*task initiation.*planning.*time",
        )
        self.assertNotIn("[TODO", SKILL_TEXT)
        self.assertNotIn("TODO", SKILL_TEXT)

    def test_skill_routes_by_bottleneck_instead_of_dumping_advice(self):
        self.assertContainsAll(
            SKILL_TEXT,
            (
                "task initiation",
                "planning",
                "prioritisation",
                "time awareness",
                "working memory",
                "attention",
                "completion",
                "emotional overload",
                "one bottleneck",
                "paste the list unchanged",
            ),
        )
        self.assertRegex(SKILL_TEXT.lower(), r"(do not|never).*dump.*(tips|strategies|advice)")

    def test_prioritisation_has_low_load_intake_and_a_tie_breaker(self):
        self.assertContainsAll(
            SKILL_TEXT,
            (
                "paste the list unchanged",
                "at most one follow-up",
                "imminent irreversible consequence",
                "hard deadline",
                "blocking another person",
                "effort as the final tie-breaker",
                "one **Now**",
                "up to two **Next**",
                "Parked",
            ),
        )

    def test_skill_defines_a_proactive_but_consent_preserving_loop(self):
        self.assertContainsAll(
            SKILL_TEXT,
            (
                "proactive trigger",
                "one next action",
                "under two minutes",
                "visible state",
                "check back",
                "ask permission",
                "persistent reminders",
                "contact another person",
            ),
        )
        self.assertRegex(SKILL_TEXT.lower(), r"(do the work|act for the user).*when.*(possible|authorised)")

    def test_progress_and_check_ins_are_truthful_and_bounded(self):
        self.assertContainsAll(
            SKILL_TEXT,
            (
                "Prepared",
                "Ready",
                "do not imply that the user completed",
                "cannot know whether the user has finished",
                "user reports",
                "maximum duration",
                "maximum number of check-ins",
                "stop at any time",
                "after silence",
                "cancel",
            ),
        )

    def test_skill_preserves_safety_autonomy_and_dignity(self):
        self.assertContainsAll(
            SKILL_TEXT,
            (
                "do not diagnose",
                "do not recommend medication changes",
                "not a substitute for professional care",
                "urgent safety",
                "non-judgmental",
                "not laziness",
                "user can decline",
            ),
        )
        self.assertNotIn("just try harder", SKILL_TEXT.lower())

    def test_medication_questions_include_an_already_taken_branch(self):
        self.assertContainsAll(
            SKILL_TEXT,
            (
                "already taken",
                "local poison information service",
                "emergency care",
                "severe symptoms",
            ),
        )

    def test_evidence_base_exists_and_labels_strength(self):
        self.assertTrue(EVIDENCE_PATH.is_file())
        evidence = EVIDENCE_PATH.read_text(encoding="utf-8")
        self.assertContainsAll(
            evidence,
            (
                "Evidence tiers",
                "guideline-backed",
                "trial-supported",
                "indirect or preference-based",
                "body doubling",
                "limited direct evidence",
                "coaching",
                "preliminary or suggestive evidence",
                "efficacy and safety remain uncertain",
                "NICE",
                "Australian ADHD Professionals Association",
                "Cochrane",
                "Safren",
                "Solanto",
                "Knouse",
            ),
        )
        for url in (
            "https://www.nice.org.uk/guidance/ng87/chapter/recommendations",
            "https://adhdguideline.aadpa.com.au/",
            "https://www.cochrane.org/evidence/CD010840_cognitive-behavioural-interventions-attention-deficit-hyperactivity-disorder-adhd-adults",
            "https://pubmed.ncbi.nlm.nih.gov/20736471/",
            "https://pubmed.ncbi.nlm.nih.gov/20231319/",
            "https://pubmed.ncbi.nlm.nih.gov/28504540/",
            "https://pubmed.ncbi.nlm.nih.gov/19276311/",
            "https://pubmed.ncbi.nlm.nih.gov/41538184/",
        ):
            with self.subTest(url=url):
                self.assertIn(url, evidence)

    def test_dual_platform_manifests_and_repo_registries_are_complete(self):
        for relative in (
            ".codex-plugin/plugin.json",
            ".claude-plugin/plugin.json",
        ):
            manifest = json.loads((PLUGIN_ROOT / relative).read_text(encoding="utf-8"))
            self.assertEqual(manifest["name"], "executive-dysfunction")
            self.assertEqual(manifest["version"], "0.1.0")

        registry = json.loads((REPO_ROOT / "skills.json").read_text(encoding="utf-8"))
        entries = [
            item for item in registry["skills"] if item["name"] == "executive-dysfunction"
        ]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["plugin"], "plugins/executive-dysfunction")
        self.assertEqual(entries[0]["plugin_version"], "0.1.0")

        compatibility = REPO_ROOT / "skills" / "executive-dysfunction"
        self.assertTrue(compatibility.is_symlink())
        self.assertEqual(compatibility.resolve(), SKILL_ROOT.resolve())


if __name__ == "__main__":
    unittest.main()
