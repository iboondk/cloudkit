# Proof directory

This directory holds output that was actually captured on a local machine. Captured output from local runs.

## Files

- **`unittest.txt`** is the verbose output of `python3 -m unittest discover -s tests -v`, captured from a run with all tests passing. A test checks that the test count in WRITEUP.md and DEMO.md matches this file. Regenerate it after any test change with `python3 -m unittest discover -s tests -v > docs/proof/unittest.txt.new && mv docs/proof/unittest.txt.new docs/proof/unittest.txt`, and run it twice, because the test reads the file the run replaces.
- **`terraform-validate.txt`** is an older capture of `scripts/validate.sh` from a machine that had terraform. The most recent verification could not reproduce it, because terraform is not installed there. Treat it as unverified until `scripts/validate.sh` is re-run with terraform on PATH and the file is regenerated.
- **`validate-skipped.txt`** is a representative `validate.sh` run on a machine without terraform. It contains only SKIP lines and exit code 0. A SKIP is not a pass.
- **`teardown-dry-run.txt`** is the real output of `bash scripts/teardown.sh --dry-run`. Dry-run contacts nothing: it invokes no terraform and no aws command.
- **`validate-<UTC timestamp>.txt`** files are written by `scripts/validate.sh` each time it runs. They are ad-hoc and ignored by git (see `.gitignore`). Keep a copy under a stable name if one should be committed.

## Checks on the local machine

Local machine: macOS (Darwin 21.6.0), Python 3 with PyYAML. Terraform, ansible, tflint, shellcheck, docker and go-based linters were not on PATH for the most recent verification.

| Check | Ran? | Result |
|---|---|---|
| `terraform fmt -check -recursive terraform` | No | terraform not installed. Not verified. |
| `terraform init -backend=false` and `validate` on all seven roots | No | terraform not installed. Not verified. |
| `terraform -chdir=terraform/envs/dev test` | No | terraform not installed. Not verified. |
| `bash scripts/validate.sh` | Yes | Every Terraform, ansible, tflint and shellcheck check printed SKIP. Exit code 0. A SKIP is not a pass. |
| `python3 -m unittest discover -s tests -v` | Yes | 119 tests, all OK. Captured in `unittest.txt`. |
| `bash scripts/teardown.sh --dry-run` | Yes | Printed DRY-RUN lines only, exit 0. |
| `ansible-playbook --syntax-check` | No | ansible is not installed. |
| `tflint`, `shellcheck` | No | Not installed. |
| `actionlint`, `checkov`, `yamllint`, `ansible-lint` | No | Not installed. |
| `docker` | No | Not installed. |

Lock files: the AWS provider lock files were recorded on a machine with a local provider mirror, so they may hold hashes for one platform only. Before CI runs on Linux, regenerate each lock file with `terraform providers lock -platform=linux_amd64 -platform=linux_arm64 -platform=darwin_arm64` on a machine with network access.

A SKIP line is not a pass. Any check that needs a missing tool stays unverified until that tool is installed and the check runs.
