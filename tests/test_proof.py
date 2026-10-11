import os
import re
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT, read

TEARDOWN = ROOT / "scripts" / "teardown.sh"
ARCH = "docs/architecture.md"
COST = "docs/cost.md"
CONFIRM_VAR = "CLOUDKIT_CONFIRM_TEARDOWN"


def _fake_tool(directory, name):
    """Write a fake executable that creates a marker file when it is run."""
    marker = Path(directory) / f"{name}.ran"
    script = Path(directory) / name
    script.write_text(f'#!/bin/sh\ntouch "{marker}"\nexit 0\n', encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return marker


def _run_teardown(args, directory, stdin=b""):
    """Run teardown.sh with fake terraform and aws first on PATH and the confirm var cleared."""
    env = dict(os.environ)
    env.pop(CONFIRM_VAR, None)
    env["PATH"] = directory + os.pathsep + os.environ.get("PATH", "")
    return subprocess.run(
        ["bash", str(TEARDOWN), *args],
        cwd=ROOT,
        env=env,
        input=stdin,
        capture_output=True,
        timeout=60,
    )


class TeardownScriptTest(unittest.TestCase):
    def test_exists_and_is_executable(self):
        self.assertTrue(TEARDOWN.is_file(), "scripts/teardown.sh missing")
        self.assertTrue(os.access(TEARDOWN, os.X_OK), "scripts/teardown.sh not executable")

    def test_bash_syntax_passes(self):
        result = subprocess.run(["bash", "-n", str(TEARDOWN)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_no_args_is_dry_run_and_runs_no_tools(self):
        with tempfile.TemporaryDirectory() as fake_dir:
            tf_marker = _fake_tool(fake_dir, "terraform")
            aws_marker = _fake_tool(fake_dir, "aws")
            result = _run_teardown([], fake_dir)
            stdout = result.stdout.decode("utf-8")
            self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8"))
            self.assertIn("DRY-RUN", stdout)
            for line in stdout.splitlines():
                if line.strip():
                    self.assertTrue(line.startswith("DRY-RUN"), f"non DRY-RUN line: {line!r}")
            self.assertFalse(tf_marker.exists(), "terraform was invoked in dry-run")
            self.assertFalse(aws_marker.exists(), "aws was invoked in dry-run")

    def test_explicit_dry_run_runs_no_tools(self):
        with tempfile.TemporaryDirectory() as fake_dir:
            tf_marker = _fake_tool(fake_dir, "terraform")
            aws_marker = _fake_tool(fake_dir, "aws")
            result = _run_teardown(["--dry-run"], fake_dir)
            self.assertEqual(result.returncode, 0)
            self.assertFalse(tf_marker.exists())
            self.assertFalse(aws_marker.exists())

    def test_execute_without_confirm_var_refuses(self):
        with tempfile.TemporaryDirectory() as fake_dir:
            tf_marker = _fake_tool(fake_dir, "terraform")
            aws_marker = _fake_tool(fake_dir, "aws")
            result = _run_teardown(["--execute", "--yes"], fake_dir)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(tf_marker.exists(), "terraform ran without confirmation")
            self.assertFalse(aws_marker.exists(), "aws ran without confirmation")

    def test_execute_without_typed_confirmation_refuses(self):
        with tempfile.TemporaryDirectory() as fake_dir:
            tf_marker = _fake_tool(fake_dir, "terraform")
            aws_marker = _fake_tool(fake_dir, "aws")
            env_marker = "dev"
            env = dict(os.environ)
            env[CONFIRM_VAR] = env_marker
            env["PATH"] = fake_dir + os.pathsep + os.environ.get("PATH", "")
            result = subprocess.run(
                ["bash", str(TEARDOWN), "--execute"],
                cwd=ROOT,
                env=env,
                input=b"no\n",
                capture_output=True,
                timeout=60,
            )
            self.assertEqual(result.returncode, 2)
            self.assertFalse(tf_marker.exists(), "terraform ran without typed confirmation")
            self.assertFalse(aws_marker.exists(), "aws ran without typed confirmation")

    def test_unknown_flag_exits_64(self):
        with tempfile.TemporaryDirectory() as fake_dir:
            tf_marker = _fake_tool(fake_dir, "terraform")
            aws_marker = _fake_tool(fake_dir, "aws")
            result = _run_teardown(["--nuke-everything"], fake_dir)
            self.assertEqual(result.returncode, 64)
            self.assertIn("Usage", result.stderr.decode("utf-8"))
            self.assertFalse(tf_marker.exists())
            self.assertFalse(aws_marker.exists())


class ArchitectureDocTest(unittest.TestCase):
    def setUp(self):
        self.text = read(ARCH)

    def test_has_mermaid_block(self):
        self.assertIn("```mermaid", self.text)

    def test_mentions_core_services(self):
        for word in ("CloudFront", "Fargate", "RDS", "OIDC", "SNS"):
            self.assertIn(word, self.text, f"{word} missing from architecture.md")


class CostDocTest(unittest.TestCase):
    def setUp(self):
        self.text = read(COST)

    def test_states_estimate(self):
        self.assertRegex(self.text, re.compile("estimate", re.IGNORECASE))

    def test_mentions_nat(self):
        self.assertIn("NAT", self.text)

    def test_measured_only_in_disclaimer(self):
        lowered = self.text.lower()
        total = len(re.findall(r"measured", lowered))
        in_phrase = lowered.count("not a measured bill")
        self.assertGreaterEqual(in_phrase, 1, "disclaimer 'not a measured bill' missing")
        self.assertEqual(total, in_phrase, "'measured' used outside the disclaimer phrase")


if __name__ == "__main__":
    unittest.main()
