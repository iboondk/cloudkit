#!/usr/bin/env bash
# Tear down a CloudKit environment (default: dev).
#
# Default mode is --dry-run: it prints the ordered steps, every line prefixed
# with "DRY-RUN:", and exits 0 without invoking terraform or aws.
#
# --execute runs the steps. It requires terraform and aws on PATH, the env var
# CLOUDKIT_CONFIRM_TEARDOWN set to the environment name, and either --yes or a
# typed confirmation of "destroy <env>". Otherwise it exits 2 before doing anything.
#
# terraform/bootstrap is never destroyed: its state bucket has prevent_destroy.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MODE="dry-run"
ENV_NAME="dev"
ASSUME_YES=0

usage() {
  cat <<'EOF'
Usage: teardown.sh [--dry-run|--execute] [--env <name>] [--yes]

  --dry-run    Print the ordered teardown steps and exit 0. Runs nothing. (default)
  --execute    Run the teardown. Requires:
                 - terraform and aws on PATH
                 - CLOUDKIT_CONFIRM_TEARDOWN set to the environment name (for example dev)
                 - --yes, or a typed confirmation of: destroy <env>
  --env <name> Environment to tear down (default: dev)
  --yes        Skip the typed confirmation and pass -auto-approve to terraform destroy
  -h, --help   Show this help
EOF
}

is_dry_run() { [ "$MODE" = "dry-run" ]; }

# say: print a line. In dry-run every line carries the DRY-RUN prefix.
say() {
  if is_dry_run; then
    printf 'DRY-RUN: %s\n' "$*"
  else
    printf '%s\n' "$*"
  fi
}

# run: print a command in dry-run mode, or print and execute it otherwise.
run() {
  if is_dry_run; then
    printf 'DRY-RUN: %s\n' "$*"
  else
    printf '+ %s\n' "$*"
    "$@"
  fi
}

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) MODE="dry-run" ;;
    --execute) MODE="execute" ;;
    --env)
      if [ $# -lt 2 ]; then
        echo "teardown.sh: --env needs a value" >&2
        usage >&2
        exit 64
      fi
      ENV_NAME="$2"
      shift
      ;;
    --yes) ASSUME_YES=1 ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "teardown.sh: unknown argument: $1" >&2
      usage >&2
      exit 64
      ;;
  esac
  shift
done

if [[ ! "$ENV_NAME" =~ ^[a-z0-9-]+$ ]]; then
  echo "teardown.sh: invalid environment name: $ENV_NAME" >&2
  exit 64
fi

ENV_DIR="terraform/envs/$ENV_NAME"
if [ ! -d "$ENV_DIR" ]; then
  echo "teardown.sh: no such environment directory: $ENV_DIR" >&2
  exit 64
fi

# Preflight for --execute. Every check runs before any command, so a refusal changes nothing.
if ! is_dry_run; then
  if [ "${CLOUDKIT_CONFIRM_TEARDOWN:-}" != "$ENV_NAME" ]; then
    echo "teardown.sh: refusing to execute. Set CLOUDKIT_CONFIRM_TEARDOWN=$ENV_NAME to confirm." >&2
    exit 2
  fi
  for tool in terraform aws; do
    if ! command -v "$tool" >/dev/null 2>&1; then
      echo "teardown.sh: $tool is not on PATH; nothing was run." >&2
      exit 2
    fi
  done
  if [ "$ASSUME_YES" -ne 1 ]; then
    printf "Type 'destroy %s' to continue: " "$ENV_NAME" >&2
    answer=""
    IFS= read -r answer || answer=""
    if [ "$answer" != "destroy $ENV_NAME" ]; then
      echo "teardown.sh: confirmation did not match; nothing was run." >&2
      exit 2
    fi
  fi
fi

# Resolve the bucket name. Dry-run never calls terraform, so it shows a placeholder.
if is_dry_run; then
  BUCKET="<assets-bucket>"
else
  BUCKET="$(terraform -chdir="$ENV_DIR" output -raw assets_bucket_name)"
fi

s3_cmd=(aws s3 rm "s3://${BUCKET}" --recursive)
tf_cmd=(terraform "-chdir=${ENV_DIR}" destroy -input=false)
if [ "$ASSUME_YES" -eq 1 ]; then
  tf_cmd+=(-auto-approve)
fi

say "CloudKit teardown: environment=$ENV_NAME mode=$MODE"

say "Step 1 of 3: empty the static assets bucket"
run "${s3_cmd[@]}"

say "Step 2 of 3: destroy the $ENV_NAME stack (network, db, compute, edge, observability)"
run "${tf_cmd[@]}"

say "Step 3 of 3: terraform/bootstrap is intentionally NOT destroyed"
say "  It holds the Terraform state bucket (prevent_destroy = true), the GitHub OIDC"
say "  provider and the plan/apply IAM roles. Removing it is a manual, deliberate task:"
say "  1. Review terraform/bootstrap and remove the state bucket's prevent_destroy in a reviewed change."
say "  2. Empty the state bucket, including noncurrent object versions (it is versioned)."
say "  3. Run terraform -chdir=terraform/bootstrap destroy locally with your own credentials."
say "  4. Delete the GitHub 'production' environment and any repository secrets you no longer need."

if is_dry_run; then
  say "Dry-run complete. Nothing was run. Use --execute with CLOUDKIT_CONFIRM_TEARDOWN=$ENV_NAME to run."
else
  say "Teardown finished for environment $ENV_NAME."
fi
