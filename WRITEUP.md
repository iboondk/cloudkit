# CloudKit write-up

## Problem

Tenantly is a Go API backed by PostgreSQL 16 with row-level security, plus Redis for rate limiting and caching. It has no deployment target yet. CloudKit is the reference design for running it on AWS: infrastructure as code, CI/CD without long-lived keys, host hardening and monitoring. All checks run offline without AWS credentials. The stack has not been deployed to a live account.

## Architecture

CloudFront is the public entry point. It serves `/static/*` from a private S3 bucket through Origin Access Control and forwards everything else to an Application Load Balancer. The ALB accepts port 80 only from the CloudFront prefix list. It forwards to an ECS Fargate task running the API and a Redis sidecar. RDS PostgreSQL sits in private subnets and accepts connections only from the application security group. CloudWatch provides logs, a dashboard and seven alarms. Terraform is split into five modules, a dev root and a bootstrap root.

## Key decisions

- **No NAT gateway** (ADR-0001). Tasks run in public subnets, and their security group admits only ALB traffic. This avoids about $33 per month.
- **CloudFront in front of the ALB** (ADR-0002). HTTPS works without a custom domain. The known weakness is plain HTTP between CloudFront and the ALB.
- **OIDC, no static keys** (ADR-0003). Plans run read-only on pull requests. Apply runs only from main, behind the `production` environment.
- **Redis as a sidecar** (ADR-0004). Counters and cache are disposable, so ElastiCache is deferred.
- **RDS-managed master password** (ADR-0005). The password never reaches Terraform state or tfvars.
- **Offline verification** (ADR-0006). Mock-provider plans and Python tests run without credentials.

## Results

On a local macOS machine (Python 3.10):

- The Python `unittest` suite ran 119 tests, all passing (`docs/proof/unittest.txt`).
- The teardown dry run executed nothing (`docs/proof/teardown-dry-run.txt`).
- `scripts/validate.sh` printed SKIP for terraform, ansible, tflint and shellcheck, which are not installed. Those checks are unverified, so the Terraform modules have not been fmt-checked or validated yet.

Not verified: `terraform fmt`, `validate` and `terraform test`, no plan or apply against AWS, no GitHub workflow run, no container build. No load test exists, so there is no performance claim. The cost table is an estimate from public list prices, not a measured bill.

## What I would do next

First, run `terraform providers lock` for linux_amd64 and arm64 so CI can install the AWS provider on Linux. Second, build the Tenantly image to replace the placeholder nginx image. Third, add a custom domain and ACM certificate to encrypt CloudFront-to-ALB traffic. Fourth, decide on ElastiCache and a second availability zone from measured load. Fifth, add WAF rules to CloudFront.
