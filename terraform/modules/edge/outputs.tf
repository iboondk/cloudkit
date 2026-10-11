output "distribution_id" {
  description = "ID of the CloudFront distribution."
  value       = aws_cloudfront_distribution.this.id
}

output "distribution_arn" {
  description = "ARN of the CloudFront distribution."
  value       = aws_cloudfront_distribution.this.arn
}

output "distribution_domain_name" {
  description = "Domain name of the CloudFront distribution (*.cloudfront.net)."
  value       = aws_cloudfront_distribution.this.domain_name
}

output "assets_bucket_name" {
  description = "Name of the private S3 bucket serving /static/* through CloudFront."
  value       = aws_s3_bucket.assets.bucket
}
