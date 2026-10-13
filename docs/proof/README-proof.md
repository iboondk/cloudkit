# Proof directory

This directory holds output that was actually captured on a local machine. Nothing here is written by hand. If a check did not run, its file says so, and a SKIP line is never reported as a pass.

## Files

- **`validate-<UTC timestamp>.txt`** files are written only by `scripts/validate.sh`, one per run. They are git-ignored (`docs/proof/validate-2*.txt` in `.gitignore`).
- **`validate-local-terraform-run.txt`** is a verbatim copy (ANSI colour codes stripped) of the `validate.sh` log from a run on 2026-10-13 (UTC 20:21:07), after the provider block move and the test fix. It used Terraform 1.10.5 from `/Volumes/Hazel/caches/bin` with a local filesystem provider mirror (`/Volumes/Hazel/tfcheck/cli.tfrc`) and `AWS_*` variables unset. Exit code 0. It shows `terraform fmt -check`, `init` and `validate` passing in all modules and roots, and the offline `terraform test` passing (2 of 2). Only ansible-galaxy and the ansible syntax check ran beyond terraform. tflint and shellcheck printed SKIP lines.
- **`validate-local-run.txt`** is a verbatim copy of the `validate.sh` log from the run on 2026-10-11 (UTC 20:30:50). It is copied here because the timestamped files are git-ignored. The file is not SKIP-only: the ansible syntax check ran and passed. Terraform, tflint and shellcheck printed SKIP lines.
- **`teardown-dry-run.txt`** is the real output of `bash scripts/teardown.sh --dry-run`, re-captured on 2026-10-13 (UTC 21:08) and identical to a second run of the same command. Dry-run contacts nothing: it invokes no terraform and no aws command. Every line starts with `DRY-RUN:`.
- **`validate-20261013T210742Z.txt`** is the `validate.sh` log from the run on 2026-10-13 (UTC 21:07:42), with no terraform on PATH. It is not SKIP-only: the ansible-galaxy and ansible-playbook `--syntax-check` steps ran and exited 0. Terraform, tflint and shellcheck printed SKIP lines. Like all timestamped logs it is git-ignored. Only `validate.sh` writes files named `validate-<UTC timestamp>.txt`.
- **`unittest.txt`** is the verbose capture of `python3 -m unittest discover -s tests -v`, taken on 2026-10-14. It records 129 tests. `WRITEUP.md` and `DEMO.md` quote that count, and `tests/test_packaging.py` checks they match this file. Regenerate this file only together with those two counts.
- **`unverified/`** holds captures whose origin cannot be re-verified on the build machine. They are not evidence that any check passes.
  - `unverified/validate-skipped.txt` is a SKIP-only log from an earlier build-machine run. It is not this run's output. The run on 2026-10-11 was not SKIP-only, and its real output is `validate-local-run.txt`. Its origin is not re-verified here.

## Checks on the build machine

Build machine: macOS (Darwin 21.6.0), bash, Python 3.10 with PyYAML. Checked with `command -v`: `tflint`, `shellcheck`, `actionlint`, `docker` and `ansible-playbook` are not on PATH. `terraform` is not on the default PATH either, but a binary exists at `/Volumes/Hazel/caches/bin/terraform`. The validation run above put it on PATH explicitly. An ansible-core install exists in the venv at `/Volumes/Hazel/caches/ansible-venv`, and `validate.sh` uses it through `python -m ansible`.

| Check | Ran? | Result |
|---|---|---|
| `terraform fmt -check -recursive terraform` | Yes | Passed, with Terraform 1.10.5 (see `validate-local-terraform-run.txt`). |
| `terraform init -backend=false` and `validate` in every module and root | Yes | All passed, with the local mirror. |
| `terraform -chdir=terraform/envs/dev test` (offline mock plan) | Yes | Passed, 2 of 2 runs (`plan_dev`, `alarm_email_subscribes`). Mock provider, plan only. |
| `ansible-galaxy collection install -r ansible/requirements.yml` | Yes | Output: "Nothing to do. All requested collections are already installed." Exit 0. |
| `ansible-playbook --syntax-check -i inventory.example.ini site.yml` | Yes | Printed `playbook: site.yml` with no errors. Passed. |
| `tflint --recursive` | No | tflint not installed. `SKIP` printed. |
| `shellcheck scripts/*.sh` | No | shellcheck not installed. `SKIP` printed. Not verified. |
| `bash scripts/validate.sh` | Yes | Exit code 0 with Terraform on PATH, log saved as `validate-local-terraform-run.txt`. tflint and shellcheck were SKIPped and are not verified. An earlier run without terraform is in `validate-local-run.txt`. |
| `python3 -m unittest discover -s tests -v` | Yes | Ran 129 tests, all OK, on 2026-10-14. This run was saved as `docs/proof/unittest.txt` on 2026-10-14. |
| `bash scripts/teardown.sh --dry-run` | Yes | Printed DRY-RUN lines only, exit 0 (re-run 2026-10-13). Saved as `teardown-dry-run.txt`. |
| `bash -n scripts/teardown.sh` | Yes | Passed (also checked by `tests/test_proof.py`). |
| `actionlint`, `checkov`, `yamllint`, `ansible-lint`, `docker` | No | Not run. Not verified. |

A SKIP line is not a pass. Any check that needs a missing tool stays unverified until that tool is installed and the check runs.

