output "cluster_name" {
  description = "Name of the ECS cluster."
  value       = aws_ecs_cluster.this.name
}

output "service_name" {
  description = "Name of the ECS Fargate service."
  value       = aws_ecs_service.this.name
}

output "alb_dns_name" {
  description = "DNS name of the application load balancer (CloudFront origin)."
  value       = aws_lb.this.dns_name
}

output "alb_arn_suffix" {
  description = "ARN suffix of the ALB, for CloudWatch dimensions."
  value       = aws_lb.this.arn_suffix
}

output "target_group_arn_suffix" {
  description = "ARN suffix of the target group, for CloudWatch dimensions."
  value       = aws_lb_target_group.this.arn_suffix
}

output "log_group_name" {
  description = "Name of the CloudWatch log group for the app and redis containers."
  value       = aws_cloudwatch_log_group.this.name
}

output "task_execution_role_arn" {
  description = "ARN of the ECS task execution role."
  value       = aws_iam_role.task_execution.arn
}
