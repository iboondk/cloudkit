# ADR-0003: GitHub Actions authenticates to AWS with OIDC, not static keys

## Status

Accepted, 2026-10-11

## Context

CI needs AWS credentials to read Terraform state and, on main, to apply the dev stack. Long-lived access keys stored as GitHub secrets are a common source of leaked credentials.

## Decision

Create an IAM OIDC identity provider for GitHub in `terraform/bootstrap`, plus two roles:

- `cloudkit-plan` trusts `pull_request` subjects and is read-only plus state access.
- `cloudkit-apply` trusts only `ref:refs/heads/main` and is gated by the `production` GitHub environment.

Workflows request short-lived STS credentials with `id-token: write`. No access key is stored in the repository or in GitHub secrets.

## Consequences

- No static AWS key exists to rotate or leak.
- The trust policies are the security boundary. A mistake in the `sub` condition would widen access, so the offline tests check the trust conditions as text.
- Bootstrap uses local state and is applied once by a person. CI never applies it.
- Forks and unconfigured repositories skip the AWS steps, because the role ARN variable is unset.
