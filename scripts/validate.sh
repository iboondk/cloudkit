#!/usr/bin/env bash
# Static validation for the CloudKit repo.
# Runs terraform fmt/init/validate/test when terraform is installed, and
# prints SKIP lines for optional tools that are missing. Output is teed to
# docs/proof/validate-<UTC timestamp>.txt.
#
# Failure handling: run_checks is called on the left of a pipeline, where
# bash ignores errexit inside the function body. So every check records its
# own failure in `fail` instead of relying on `set -e`, and run_checks returns
# non-zero if any check failed. A missing optional tool is a SKIP, not a failure.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

run_checks() {
  local fail=0

  if command -v terraform >/dev/null 2>&1; then
    export TF_PLUGIN_CACHE_DIR="${TF_PLUGIN_CACHE_DIR:-$HOME/.terraform.d/plugin-cache}"
    mkdir -p "$TF_PLUGIN_CACHE_DIR"

    echo "== terraform fmt -check"
    terraform fmt -check -recursive terraform || fail=1

    for d in terraform/modules/* terraform/envs/dev terraform/bootstrap; do
      [ -d "$d" ] || continue
      echo "== terraform init (no backend): $d"
      terraform -chdir="$d" init -backend=false -input=false || fail=1
      echo "== terraform validate: $d"
      terraform -chdir="$d" validate || fail=1
    done

    if [ -d terraform/envs/dev/tests ]; then
      echo "== terraform test (offline mock plan): terraform/envs/dev"
      terraform -chdir=terraform/envs/dev test || fail=1
    fi
  else
    echo "SKIP: terraform not installed (terraform checks not run)"
  fi

  if command -v ansible-playbook >/dev/null 2>&1; then
    if [ -f ansible/site.yml ]; then
      # The collections (ansible.posix, community.general) are needed to resolve the
      # role's modules. ansible-core alone does not ship them.
      export ANSIBLE_COLLECTIONS_PATH="${ANSIBLE_COLLECTIONS_PATH:-$HOME/.ansible/collections}"
      mkdir -p "$ANSIBLE_COLLECTIONS_PATH" 2>/dev/null || true
      echo "== ansible-galaxy collection install -r ansible/requirements.yml"
      if command -v ansible-galaxy >/dev/null 2>&1 \
         && ansible-galaxy collection install -r ansible/requirements.yml -p "$ANSIBLE_COLLECTIONS_PATH"; then
        # Run from ansible/ so ansible.cfg (roles_path, inventory) is loaded.
        echo "== ansible-playbook --syntax-check (ansible/site.yml)"
        (cd ansible && ansible-playbook --syntax-check site.yml) || fail=1
      else
        echo "SKIP: ansible collections not installed (offline or ansible-galaxy missing); ansible --syntax-check not run"
      fi
    fi
  else
    echo "SKIP: ansible not installed"
  fi

  if command -v tflint >/dev/null 2>&1; then
    echo "== tflint --recursive"
    tflint --recursive || fail=1
  else
    echo "SKIP: tflint not installed"
  fi

  if command -v shellcheck >/dev/null 2>&1; then
    echo "== shellcheck scripts/*.sh"
    shellcheck scripts/*.sh || fail=1
  else
    echo "SKIP: shellcheck not installed"
  fi

  return "$fail"
}

mkdir -p docs/proof
LOG="docs/proof/validate-$(date -u +%Y%m%dT%H%M%SZ).txt"
rc=0
run_checks 2>&1 | tee "$LOG" || rc=$?
echo "validate exit code: $rc" | tee -a "$LOG"
exit "$rc"
