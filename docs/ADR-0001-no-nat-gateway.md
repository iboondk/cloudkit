# ADR-0001: No NAT gateway; Fargate tasks in public subnets

## Status

Accepted, 2026-10-11

## Context

Fargate tasks need outbound access to pull container images from a registry. The conventional design puts tasks in private subnets behind a NAT gateway. A single NAT gateway costs about $33 per month before data processing charges (0.045 USD/h x 730 h, plus 0.045 USD per GB processed). For a dev stack with low traffic, that is a large share of the total cost estimate in `docs/cost.md`.

## Decision

Run the ECS tasks in public subnets with a public IP address. The task security group admits traffic on `container_port` only from the ALB security group, so the public IP is not a direct ingress path. RDS stays in private subnets with no route to the internet gateway.

## Consequences

- Saves roughly $33 per month per NAT gateway, plus data processing charges.
- Each task carries a public IPv4 address, which is billed (about $0.005 per hour). This is counted in `docs/cost.md`.
- Ingress is still restricted by security groups, but tasks are reachable on the network. A WAF or a private-subnet design is the upgrade path if the threat model changes.
- The decision is revisited if the service needs outbound traffic filtering or egress to fixed IP addresses.
