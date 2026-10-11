# Proof directory

This directory holds output that was actually captured on a local machine. Nothing here is written by hand. If a check did not run, its file says so, and a SKIP line is never reported as a pass.

## Files

- **`validate-<UTC timestamp>.txt`** files are written only by `scripts/validate.sh`, one per run. They are git-ignored (`docs/proof/validate-2*.txt` in `.gitignore`).
- **`validate-local-run.txt`** is a verbatim copy of the `validate.sh` log from the run on 2026-10-11 (UTC 20:30:50). It is copied here because the timestamped files are git-ignored. The file is not SKIP-only: the ansible syntax check ran and passed. Terraform, tflint and shellcheck printed SKIP lines.
- **`teardown-dry-run.txt`** is the real output of `bash scripts/teardown.sh --dry-run`, captured on 2026-10-11. Dry-run contacts nothing: it invokes no terraform and no aws command. Every line starts with `DRY-RUN:`.
- **`unittest.txt`** is the verbose capture of `python3 -m unittest discover -s tests -v`, taken on 2026-10-11. It records 123 tests. `WRITEUP.md` and `DEMO.md` quote that count, and `tests/test_packaging.py` checks they match this file. Regenerate this file only together with those two counts.
- **`unverified/`** holds captures whose origin cannot be re-verified on the build machine. They are not evidence that any check passes.
  - `unverified/terraform-validate.txt` is an older capture of `scripts/validate.sh` from a machine that had terraform. It reports fmt, validate and offline tests passing. The most recent verification could not reproduce it, because terraform is not installed on the build machine. Treat it as unverified until `scripts/validate.sh` is re-run with terraform on PATH and the file is regenerated.
  - `unverified/validate-skipped.txt` is a SKIP-only log from an earlier build-machine run. It is not this run's output. The run on 2026-10-11 was not SKIP-only, and its real output is `validate-local-run.txt`. Its origin is not re-verified here.

## Checks on the build machine

Build machine: macOS (Darwin 21.6.0), bash, Python 3.10 with PyYAML. Checked with `command -v`: `terraform`, `tflint`, `shellcheck`, `actionlint`, `docker` and `ansible-playbook` are not on PATH. An ansible-core install exists in the venv at `/Volumes/Hazel/caches/ansible-venv`, and `validate.sh` uses it through `python -m ansible`.

| Check | Ran? | Result |
|---|---|---|
| `terraform fmt -check -recursive terraform` | No | terraform not installed. `SKIP` printed. Not verified. |
| `terraform init -backend=false` and `validate` in every module and root | No | terraform not installed. Not verified. |
| `terraform -chdir=terraform/envs/dev test` (offline mock plan) | No | terraform not installed. Not verified. |
| Linux `terraform init` in `terraform/envs/dev` and `terraform/bootstrap` (CI job `terraform-offline`) | No | Expected to fail. The lock files record only a `darwin_amd64` checksum. See the note at the top of `README.md`. |
| `ansible-galaxy collection install -r ansible/requirements.yml` | Yes | Output: "Nothing to do. All requested collections are already installed." Exit 0. |
| `ansible-playbook --syntax-check -i inventory.example.ini site.yml` | Yes | Printed `playbook: site.yml` with no errors. Passed. |
| `tflint --recursive` | No | tflint not installed. `SKIP` printed. |
| `shellcheck scripts/*.sh` | No | shellcheck not installed. `SKIP` printed. Not verified. |
| `bash scripts/validate.sh` | Yes | Exit code 0. Log saved as `validate-local-run.txt`. Terraform and tflint checks were SKIPped and are not verified. |
| `python3 -m unittest discover -s tests -v` | Yes | Ran 123 tests, all OK, on 2026-10-11. This run was saved as `docs/proof/unittest.txt` on 2026-10-11. |
| `bash scripts/teardown.sh --dry-run` | Yes | Printed DRY-RUN lines only, exit 0. Saved as `teardown-dry-run.txt`. |
| `bash -n scripts/teardown.sh` | Yes | Passed (also checked by `tests/test_proof.py`). |
| `actionlint`, `checkov`, `yamllint`, `ansible-lint`, `docker` | No | Not run. Not verified. |

A SKIP line is not a pass. Any check that needs a missing tool stays unverified until that tool is installed and the check runs.

Lock files: the AWS provider lock files in `terraform/envs/dev` and `terraform/bootstrap` were recorded on a machine with a local provider mirror, so each holds a hash for `darwin_amd64` only. An older capture (`unverified/terraform-validate.txt`) contains Terraform's own warning that this will fail on other platforms. Before CI can pass on Linux, regenerate each lock file with `terraform providers lock -platform=linux_amd64 -platform=linux_arm64 -platform=darwin_amd64 -platform=darwin_arm64` on a machine with network access. This has not been done.
