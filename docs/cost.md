# CloudKit monthly cost estimate

**Read this first.** The table below is estimates derived from public AWS pricing pages; not a measured bill; verify with the AWS Pricing Calculator. Nothing here reflects real spend. Check your own billing console before you rely on any number.

Basis: us-east-1, on-demand list prices, 730 hours per month, the dev stack in `terraform/envs/dev`, and low traffic. Prices change. The USD figures are rounded.

## Free tier caveat

AWS free-tier terms changed for accounts created after 2025-07-15. Those accounts use a credit-based plan instead of the classic 12-month free tier described in the column below. The free-tier column reflects the classic 12-month terms. Check which plan your own account is on before you rely on any free-tier entry.

## Table

| Component | Assumption | Free tier (12-month new account) | Est. USD/month after free tier |
|---|---|---|---|
| Fargate | 0.25 vCPU and 0.5 GB, 1 task, 730 h (x86, Linux; $0.04048/vCPU-h and $0.004445/GB-h) | None | ~9.01 |
| ALB | 1 Application Load Balancer, 730 h, 1 LCU average | Possibly 750 h/mo ELB hours and 15 LCU in year 1. Verify in your account | ~22.27 |
| Public IPv4 | 3 addresses (ALB 2 + task 1), 730 h each at $0.005/h | Limited EC2 allowance only. Verify whether it covers these addresses | ~10.95 |
| RDS PostgreSQL | db.t4g.micro, single-AZ, 20 GB gp3 storage, 730 h | 750 h/mo and 20 GB of eligible micro instance use in year 1. Verify eligibility | ~13.98 (instance ~11.68 + storage ~2.30) |
| Secrets Manager | 1 secret (the RDS-managed master password), negligible API calls | None | ~0.40 |
| CloudFront | Low traffic, under 5 GB transfer and about 1M requests per month, PriceClass_100 | Always-free tier: 1 TB transfer and 10M requests per month | ~0.00 to 0.60 |
| S3 (assets + state) | About 1 GB of assets and under 100 MB of state, Standard storage, low request count | 5 GB Standard storage for year 1 | ~0.05 |
| CloudWatch | 1 dashboard, 7 alarms, logs about 1 GB per month with 7-day retention | Always-free: 3 dashboards, 10 alarms, 5 GB log ingestion | ~0.00 to 1.00 (mostly log ingestion) |
| SNS email | 1 topic, a few alarm emails per month | Always-free: 1,000 email deliveries per month | ~0.00 |
| NAT gateway | **NOT used.** Tasks use public IPs and the internet gateway instead | Not applicable | $0. Avoided cost of about $33/month for one NAT gateway (0.045/h x 730), plus $0.045/GB processed |
| ElastiCache | **NOT used.** Redis runs as a sidecar in the task | Not applicable | $0. Scale-up path would add a cache node, for example cache.t4g.micro at about $0.016/h |
| **Total** | Sum of the rows above, dev stack | Year-1 free tier covers RDS, S3, CloudFront, CloudWatch and SNS. Fargate, public IPv4 and Secrets Manager stay billed. The ALB depends on your plan | **About $57 to $58 per month** (the rows above sum to $56.7 to $58.3, using the low and high end of the CloudFront and CloudWatch ranges) |

## Notes

- The total excludes data transfer beyond the always-free tier, RDS automated backup storage beyond the default retention, Route 53 (not used), and tax.
- The ALB (~$22), RDS (~$14) and public IPv4 (~$11) rows are the largest fixed costs, followed by Fargate (~$9). Secrets Manager is about $0.40. The two public IPv4 addresses for the ALB are billed whether or not traffic flows.
- Moving tasks behind a NAT gateway would add roughly $33 per gateway per month. That is why the design avoids NAT.
- Single-AZ RDS is the cheapest option. Multi-AZ roughly doubles the RDS line and is not included.
- Every figure above is an estimate, not a measured bill.
