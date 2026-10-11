# CloudKit architecture

CloudKit deploys the Tenantly API on AWS (us-east-1) with Terraform, GitHub Actions and OIDC. The diagram below shows the dev stack as defined in `terraform/envs/dev`. The stack has not been deployed to a live account.

```mermaid
flowchart LR
  users["Users"]
  cf["CloudFront<br/>HTTPS, PriceClass_100"]
  s3[("S3 assets bucket<br/>private, OAC")]
  gha["GitHub Actions"]
  roles["IAM roles<br/>cloudkit-plan (PRs, read-only)<br/>cloudkit-apply (main only)"]
  state[("Terraform state S3 bucket<br/>versioned, encrypted")]

  subgraph VPC["VPC 10.20.0.0/16 (2 AZs, no NAT gateway)"]
    subgraph PUB["Public subnets"]
      alb["ALB :80<br/>SG: CloudFront prefix list only"]
      subgraph ECS["ECS Fargate service (task has public IP)"]
        app["app container :8080"]
        redis["redis sidecar<br/>ephemeral"]
      end
    end
    subgraph PRIV["Private subnets"]
      rds[("RDS PostgreSQL 16<br/>db.t4g.micro, single-AZ")]
    end
  end

  sm["Secrets Manager<br/>RDS-managed secret"]
  cwl["CloudWatch Logs<br/>7-day retention"]
  dash["CloudWatch dashboard"]
  alarms["CloudWatch alarms (7)"]
  sns["SNS topic<br/>optional email"]

  users -->|"HTTPS"| cf
  cf -->|"default /*"| alb
  cf -->|"/static/* via OAC"| s3
  alb -->|"8080, ALB SG only"| app
  app --- redis
  app -->|"5432, app SG only"| rds
  app -.->|"DB credentials"| sm
  app -.->|"stdout logs"| cwl
  cwl --> dash
  alarms -->|"ALARM / OK"| sns

  gha -->|"OIDC, short-lived STS"| roles
  roles -->|"state + lock"| state
```

## Request flow

1. A user requests the CloudFront domain over HTTPS (default `*.cloudfront.net` certificate).
2. Requests for `/static/*` are served from the private S3 assets bucket through Origin Access Control.
3. All other requests go to the ALB over HTTP. The ALB security group admits port 80 only from the CloudFront origin-facing managed prefix list.
4. The ALB forwards to the ECS task on `container_port` (8080). The task security group admits that port only from the ALB security group.
5. The Go app reads PostgreSQL settings from `DB_*` variables. `DB_USER` and `DB_PASSWORD` come from the RDS-managed secret in Secrets Manager.
6. The app talks to the Redis sidecar on `localhost:6379` for rate limiting and cache.
7. RDS accepts 5432 only from the app security group. It has no route to the internet.

## Deploy flow

- **Pull request:** `terraform-plan.yml` assumes the read-only `cloudkit-plan` role through OIDC and runs fmt, validate, the offline mock plan, and a plan with state read access.
- **Merge to main:** `terraform-apply.yml` assumes `cloudkit-apply` through OIDC. That role trusts only `ref:refs/heads/main` and is gated by the `production` GitHub environment.
- **Bootstrap:** `terraform/bootstrap` uses local state and is applied once by a person. CI never applies it.
- **Image:** the app image is referenced by `var.container_image`. Its build and push are outside this repository.

## Security notes

- **No NAT gateway.** Tasks sit in public subnets with public IPs and pull images over the internet gateway. Their security group admits only ALB traffic. RDS stays in private subnets.
- **ALB restricted to CloudFront.** Port 80 is allowed only from the CloudFront managed prefix list.
- **RDS-managed master password** (`manage_master_user_password = true`). No password is in Terraform state or in tfvars.
- **OIDC, no static keys.** GitHub gets short-lived STS credentials. No long-lived AWS access key is stored in the repository or in GitHub secrets.
- **Least-privilege roles.** The plan role is read-only plus state access. The apply role is reachable only from `main`.
- **Secrets stay out of the repo.** `.env`, `backend.hcl` and `terraform.tfvars` are git-ignored. Only `*.example` placeholders are committed.

## Known limits

- **CloudFront to ALB is plain HTTP** inside AWS. The fix is a custom domain with an ACM certificate on the ALB, which is documented as an upgrade and not built.
- **Single-AZ RDS.** `db.t4g.micro` runs in one availability zone. An AZ outage stops the database. Multi-AZ is a cost and config change.
- **Redis sidecar is ephemeral.** Rate-limit counters and cache are lost when the task restarts. ElastiCache is the scale-up path.
- **No WAF.** The ALB and CloudFront have no web application firewall rules.
- **Public tasks.** Tasks have public IPs (the cost of avoiding NAT). Ingress is still limited to the ALB security group.
- **No measured performance data.** No load tests have been run. Capacity figures are not claimed.

## One-off migration task

Migrations (`cmd/migrate` in the Tenantly API) run as a one-off Fargate task that reuses the service's task definition with a command override. This is documented only. It has never been run here.

```bash
aws ecs run-task \
  --cluster cloudkit-dev-cluster \
  --task-definition <task-family-or-arn> \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[<public-subnet-id>],securityGroups=[<app-security-group-id>],assignPublicIp=ENABLED}" \
  --overrides '{"containerOverrides":[{"name":"app","command":["<migrate-command>"]}]}'
```

Replace the placeholders with values from `terraform output` and the ECS console. Do not run this against a real account from this repository without a reviewed change.
