# ADR-0005: RDS-managed master password in Secrets Manager

## Status

Accepted, 2026-10-11

## Context

The PostgreSQL master password must reach the app without appearing in Terraform state, in tfvars, or in the repository. Any value Terraform generates ends up in state.

## Decision

Set `manage_master_user_password = true` on the RDS instance. RDS generates the password and stores it in a Secrets Manager secret. The ECS task definition injects `DB_USER` and `DB_PASSWORD` from that secret's `username` and `password` keys.

## Consequences

- The password never enters Terraform state or tfvars.
- Secrets Manager is a small paid line item (about $0.40 per month for one secret), listed in `docs/cost.md`.
- Rotation is handled by RDS and Secrets Manager, not by this repository.
- The app reads the injected variables and does not need the secret ARN itself.
