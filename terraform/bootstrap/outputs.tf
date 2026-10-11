output "state_bucket_name" {
  description = "Name of the Terraform state bucket. Set this as the TF_STATE_BUCKET repository variable."
  value       = aws_s3_bucket.state.bucket
}

output "oidc_provider_arn" {
  description = "ARN of the GitHub Actions OIDC identity provider."
  value       = aws_iam_openid_connect_provider.github.arn
}

output "plan_role_arn" {
  description = "Role ARN for the plan workflow. Set this as the AWS_PLAN_ROLE_ARN repository variable."
  value       = aws_iam_role.plan.arn
}

output "apply_role_arn" {
  description = "Role ARN for the apply workflow. Set this as the AWS_APPLY_ROLE_ARN repository variable."
  value       = aws_iam_role.apply.arn
}
