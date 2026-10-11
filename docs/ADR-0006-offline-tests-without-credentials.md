# ADR-0006: Verify Terraform offline with mock providers and static tests

## Status

Accepted, 2026-10-11

## Context

The repository must be checkable without an AWS account, and nothing here is deployed by CI. A real `terraform plan` needs credentials and API calls. Tests that depend on credentials would fail for forks and for anyone without access to the account.

## Decision

Two layers run without credentials:

1. `terraform test` in `terraform/envs/dev` with `mock_provider "aws"` and `command = plan`. Mock data sources are declared in `tests/plan.tftest.hcl`. Only plans run, never applies.
2. Python `unittest` in `tests/`, which parses HCL with regular expressions and YAML with PyYAML. It also checks repository hygiene: no AWS key patterns, no secret assignments, and no `terraform apply` outside the apply workflow.

`scripts/validate.sh` runs the Terraform and Ansible checks when those tools exist and prints `SKIP:` lines when they do not. A skip is never reported as a pass.

## Consequences

- Structural and offline checks run on any machine with Python 3 and PyYAML.
- Mock plans prove the configuration plans against a stubbed provider. They do not prove that AWS accepts the resources.
- Some checks are regex based, so they can miss syntax errors. `terraform validate` and `ansible-playbook --syntax-check` cover those where the tools are installed.
