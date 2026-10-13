import re
import unittest

from helpers import ROOT, load_yaml, read

README = "README.md"
DEMO = "DEMO.md"
WRITEUP = "WRITEUP.md"
CI_WF = ".github/workflows/ci.yml"
ADR_GLOB = "docs"
UNITTEST_PROOF = "docs/proof/unittest.txt"


class PackagingTest(unittest.TestCase):
    def test_deliverables_exist(self):
        for rel in (README, DEMO, WRITEUP, CI_WF, "LICENSE"):
            self.assertTrue((ROOT / rel).is_file(), f"missing {rel}")

    def test_readme_has_mermaid_diagram(self):
        text = read(README)
        self.assertIn("```mermaid", text)
        self.assertIn("flowchart", text)

    def test_readme_has_badge_placeholder_for_ci(self):
        text = read(README)
        self.assertIn("actions/workflows/ci.yml/badge.svg", text)

    def test_readme_quick_start_is_credential_free(self):
        text = read(README)
        self.assertIn("python3 -m unittest discover -s tests", text)
        self.assertIn("Docker Compose is not applicable", text)

    def test_readme_links_resolve(self):
        text = read(README)
        for target in re.findall(r"\]\((?!https?://|#)([^)]+)\)", text):
            path = target.split("#", 1)[0]
            self.assertTrue((ROOT / path).exists(), f"broken link in README: {target}")

    def test_demo_has_numbered_steps(self):
        steps = re.findall(r"^\d+\. ", read(DEMO), re.MULTILINE)
        self.assertGreaterEqual(len(steps), 10)

    def test_writeup_word_count_is_about_400(self):
        words = len(read(WRITEUP).split())
        self.assertTrue(350 <= words <= 450, f"WRITEUP has {words} words")

    def test_writeup_has_required_sections(self):
        text = read(WRITEUP)
        for heading in ("## Problem", "## Architecture", "## Key decisions", "## Results", "## What I would do next"):
            self.assertIn(heading, text)

    def test_adrs_exist_with_required_sections(self):
        adrs = sorted((ROOT / ADR_GLOB).glob("ADR-*.md"))
        self.assertGreaterEqual(len(adrs), 4)
        for path in adrs:
            text = path.read_text(encoding="utf-8")
            for heading in ("## Status", "## Context", "## Decision", "## Consequences"):
                self.assertIn(heading, text, f"{path.name} lacks {heading}")

    def test_ci_workflow_is_credential_free(self):
        data = load_yaml(CI_WF)
        self.assertEqual(data["permissions"], {"contents": "read"})
        self.assertNotIn("id-token", read(CI_WF))
        self.assertNotIn("aws-actions", read(CI_WF))
        for name, job in data["jobs"].items():
            self.assertIn("steps", job, f"job {name} has no steps")

    def test_ci_runs_unit_tests_and_teardown_dry_run(self):
        text = read(CI_WF)
        self.assertIn("python -m unittest discover -s tests", text)
        self.assertIn("scripts/teardown.sh --dry-run", text)

    def test_test_count_matches_captured_run_in_docs(self):
        # The count in the write-up and the demo script must equal the captured unittest run.
        captured = re.search(r"^Ran (\d+) tests?", read(UNITTEST_PROOF), re.MULTILINE)
        self.assertIsNotNone(captured, f"no 'Ran N tests' line in {UNITTEST_PROOF}")
        expected = captured.group(1)
        for rel in (WRITEUP, DEMO):
            counts = re.findall(r"(\d+) tests\b", read(rel))
            self.assertTrue(counts, f"{rel} states no test count")
            for count in counts:
                self.assertEqual(count, expected, f"{rel} says {count} tests, run says {expected}")

    def test_root_lock_files_hold_registry_zh_hashes(self):
        # A lock file with only h1 hashes (one local-mirror checksum) fails `terraform init`
        # on other platforms. A zh: entry is the registry's per-zip hash, so require one.
        roots = sorted((ROOT / "terraform").glob("**/.terraform.lock.hcl"))
        roots = [p for p in roots if "modules" not in p.parts]
        self.assertTrue(roots, "no root lock files found under terraform/")
        for path in roots:
            text = path.read_text(encoding="utf-8")
            rel = path.relative_to(ROOT)
            self.assertIn('provider "registry.terraform.io/', text, f"{rel} lists no provider")
            self.assertRegex(text, r'"zh:[0-9a-f]{64}"', f"{rel} has no zh: hash for linux_amd64")

    def test_known_ci_failure_note_removed(self):
        self.assertNotIn("Known CI failure", read(README))
        self.assertNotIn("First, fix the known", read(WRITEUP))

    def test_no_compose_file_added(self):
        # CloudKit is infrastructure code, not a locally runnable service.
        self.assertFalse((ROOT / "docker-compose.yml").exists())
        self.assertFalse((ROOT / "compose.yaml").exists())


if __name__ == "__main__":
    unittest.main()
