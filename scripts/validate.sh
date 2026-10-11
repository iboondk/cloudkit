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

# Ansible helpers. The Hazel volume holds the ansible caches, so keep collections there too.
ANSIBLE_VENV_DEFAULT=/Volumes/Hazel/caches/ansible-venv

# Print the first python that can import ansible. A venv may ship ansible-core without the
# entry-point scripts (ansible-playbook, ansible-galaxy), so validate.sh falls back to
# `python -m ansible <tool>`. Prints nothing when no python has ansible.
find_ansible_python() {
  local cand
  for cand in "${ANSIBLE_PYTHON:-}" "$ANSIBLE_VENV_DEFAULT/bin/python" python3; do
    [ -n "$cand" ] || continue
    if command -v "$cand" >/dev/null 2>&1 && "$cand" -c 'import ansible' >/dev/null 2>&1; then
      command -v "$cand"
      return 0
    fi
  done
  return 0
}

# Run an ansible tool ("playbook" or "galaxy") from its entry point, or through the python
# module when only the module is installed. Arguments after the tool name are passed on.
ansible_tool() {
  local tool="$1"; shift
  if command -v "ansible-$tool" >/dev/null 2>&1; then
    "ansible-$tool" "$@"
  else
    "$ANSIBLE_PY" -m ansible "$tool" "$@"
  fi
}

run_checks() {
  local fail=0

  if command -v terraform >/dev/null 2>&1; then
    # Keep the ~600MB AWS provider off the main drive. Fall back to $HOME only when
    # the Hazel volume is not mounted.
    if [ -d /Volumes/Hazel ]; then
      _tf_cache_default=/Volumes/Hazel/caches/terraform-plugins
    else
      _tf_cache_default="$HOME/.terraform.d/plugin-cache"
    fi
    export TF_PLUGIN_CACHE_DIR="${TF_PLUGIN_CACHE_DIR:-$_tf_cache_default}"
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

  ANSIBLE_PY="$(find_ansible_python)"
  if [ -n "$ANSIBLE_PY" ] || command -v ansible-playbook >/dev/null 2>&1; then
    if [ -f ansible/site.yml ]; then
      # The collections (ansible.posix, community.general) are needed to resolve the
      # role's modules. ansible-core alone does not ship them. Keep them on the Hazel volume
      # when it is mounted, and fall back to $HOME otherwise (same rule as TF_PLUGIN_CACHE_DIR).
      if [ -d /Volumes/Hazel ]; then
        _ansible_cache_default=/Volumes/Hazel/caches/ansible
      else
        _ansible_cache_default="$HOME/.ansible/collections"
      fi
      export ANSIBLE_COLLECTIONS_PATH="${ANSIBLE_COLLECTIONS_PATH:-$_ansible_cache_default}"
      mkdir -p "$ANSIBLE_COLLECTIONS_PATH" 2>/dev/null || true
      # Galaxy stages downloads in ANSIBLE_LOCAL_TEMP (default ~/.ansible/tmp). Keep them on Hazel too.
      if [ -d /Volumes/Hazel ]; then
        export ANSIBLE_LOCAL_TEMP="${ANSIBLE_LOCAL_TEMP:-/Volumes/Hazel/caches/ansible-tmp}"
        mkdir -p "$ANSIBLE_LOCAL_TEMP" 2>/dev/null || true
      fi
      echo "== ansible-galaxy collection install -r ansible/requirements.yml"
      # A failed galaxy install is reported as SKIP, not FAIL, because the usual cause
      # on this machine is being offline. The collections are needed to resolve modules.
      if ansible_tool galaxy collection install -r ansible/requirements.yml -p "$ANSIBLE_COLLECTIONS_PATH"; then
        # Run from ansible/. ansible.cfg sits in a world-writable volume, where ansible ignores
        # it, so roles_path and config are set explicitly here rather than relying on the cfg.
        echo "== ansible-playbook --syntax-check (ansible/site.yml)"
        (
          cd ansible
          export ANSIBLE_CONFIG="$PWD/ansible.cfg"
          export ANSIBLE_ROLES_PATH="$PWD/roles"
          ansible_tool playbook --syntax-check -i inventory.example.ini site.yml
        ) || fail=1
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
