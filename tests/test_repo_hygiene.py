import os
import re
import subprocess
import unittest

from helpers import ROOT

# Attribution and secret markers are split so this file does not contain them verbatim.
CO_AUTHOR = "Co-Authored" + "-By"
GENERATED = "Generated with " + "Claude"
AWS_KEY_RE = re.compile(r"AKIA[0-9A-Z]{16}")
SECRET_RE = re.compile(r"aws_secret_access" + r"_key\s*=\s*\S")
TF_APPLY = "terraform " + "apply"
APPLY_WORKFLOW = os.path.join(".github", "workflows", "terraform-apply.yml")
SKIP_DIRS = {".git", ".terraform", "__pycache__"}


def iter_repo_files():
    # Prefer the git view (tracked plus untracked, not ignored) so local-only notes are excluded.
    try:
        out = subprocess.run(
            ["git", "-C", ROOT, "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            capture_output=True,
            check=True,
        ).stdout
        names = [n for n in out.decode("utf-8").split("\0") if n]
        if names:
            return names
    except (OSError, subprocess.CalledProcessError):
        pass
    names = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            names.append(os.path.relpath(os.path.join(dirpath, filename), ROOT))
    return names


def read_text(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace") as fh:
        return fh.read()


class RepoHygieneTest(unittest.TestCase):
    def setUp(self):
        self.files = sorted(iter_repo_files())
        self.assertTrue(self.files, "repo walk found no files")

    def test_no_aws_access_key_ids(self):
        offenders = [rel for rel in self.files if AWS_KEY_RE.search(read_text(rel))]
        self.assertEqual(offenders, [], "AWS access key ID pattern found")

    def test_no_secret_assignments(self):
        offenders = [rel for rel in self.files if SECRET_RE.search(read_text(rel))]
        self.assertEqual(offenders, [], "aws secret access key assignment found")

    def test_no_ai_attribution(self):
        offenders = []
        for rel in self.files:
            text = read_text(rel)
            if CO_AUTHOR in text or GENERATED in text:
                offenders.append(rel)
        self.assertEqual(offenders, [], "AI attribution marker found")

    def test_gitignore_covers_state_and_env(self):
        text = read_text(".gitignore")
        self.assertIn("*.tfstate", text)
        self.assertIn(".env", text)

    def test_terraform_apply_only_in_apply_workflow(self):
        offenders = []
        for rel in self.files:
            if rel == APPLY_WORKFLOW:
                continue
            parts = rel.split(os.sep)
            if parts[0] in ("docs", "tests"):
                continue
            if TF_APPLY in read_text(rel):
                offenders.append(rel)
        self.assertEqual(offenders, [], "terraform apply mentioned outside allowed files")


if __name__ == "__main__":
    unittest.main()
