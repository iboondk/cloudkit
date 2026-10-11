output "cloudfront_url" {
  description = "Public HTTPS entry point of the dev stack."
  value       = "https://${module.edge.distribution_domain_name}"
}

output "alb_dns_name" {
  description = "DNS name of the application load balancer (CloudFront origin)."
  value       = module.compute.alb_dns_name
}

output "db_address" {
  description = "Private hostname of the RDS instance."
  value       = module.db.address
}

output "dashboard_name" {
  description = "Name of the CloudWatch dashboard."
  value       = module.observability.dashboard_name
}

output "sns_topic_arn" {
  description = "ARN of the alarm SNS topic."
  value       = module.observability.sns_topic_arn
}

output "assets_bucket_name" {
  description = "Name of the private S3 assets bucket."
  value       = module.edge.assets_bucket_name
}
