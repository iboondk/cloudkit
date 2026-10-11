# ADR-0002: CloudFront in front of the ALB, with static assets served from S3

## Status

Accepted, 2026-10-11

## Context

The service needs HTTPS for users. A custom domain with an ACM certificate on the ALB would require a domain the project does not own. Static assets under `/static/*` should not consume compute capacity.

## Decision

Put a CloudFront distribution in front of everything. The distribution uses the default `*.cloudfront.net` certificate, so HTTPS needs no domain. Requests to `/static/*` go to a private S3 bucket through Origin Access Control. All other requests go to the ALB. The ALB security group admits port 80 only from the CloudFront origin-facing managed prefix list. The distribution uses `PriceClass_100`.

## Consequences

- Users get HTTPS with no certificate or domain setup.
- Static assets are cached at the edge and never reach the Fargate tasks.
- CloudFront to ALB traffic is plain HTTP inside AWS. This is a known limit, documented in `docs/architecture.md`.
- The ALB is reachable only through CloudFront, which removes direct internet access to the origin in the dev stack.
- A custom domain with ACM on the ALB is the documented upgrade.
