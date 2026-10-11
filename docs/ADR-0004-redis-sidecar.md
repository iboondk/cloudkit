# ADR-0004: Redis as an ephemeral sidecar in the ECS task, not ElastiCache

## Status

Accepted, 2026-10-11

## Context

The Tenantly API uses Redis for rate-limit counters and a cache. ElastiCache is the managed option, but it adds a cache node at a fixed hourly cost, even with no traffic.

## Decision

Run `redis:7-alpine` as a non-essential container in the same Fargate task as the app. The app reaches it on `localhost:6379`. Rate-limit counters and cache entries are treated as disposable.

## Consequences

- No cache node cost. The sidecar adds memory to the task, which is set by `var.memory`.
- Counters and cache are lost when a task restarts. This is acceptable for rate limiting and cache, and it is stated in `docs/architecture.md`.
- Scaling to more tasks gives each task its own Redis, so rate limits are per task. This is a real limit for multi-task deployments.
- ElastiCache is the scale-up path. `docs/cost.md` lists its estimated cost.
