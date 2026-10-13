# Offline plan test. Every provider call is mocked, so no AWS credentials or network
# access are needed. Only `command = plan` is used; nothing is ever applied.

mock_provider "aws" {
  mock_data "aws_availability_zones" {
    defaults = {
      names = ["us-east-1a", "us-east-1b", "us-east-1c"]
    }
  }

  mock_data "aws_ec2_managed_prefix_list" {
    defaults = {
      id = "pl-3b927c52"
    }
  }

  mock_resource "aws_db_instance" {
    defaults = {
      master_user_secret = [{
        secret_arn    = "arn:aws:secretsmanager:us-east-1:123456789012:secret:mock"
        kms_key_id    = ""
        secret_status = "active"
      }]
    }
  }

  mock_resource "aws_cloudfront_distribution" {
    defaults = {
      arn         = "arn:aws:cloudfront::123456789012:distribution/MOCK"
      domain_name = "d111111abcdef8.cloudfront.net"
    }
  }

  mock_resource "aws_iam_role" {
    defaults = {
      arn = "arn:aws:iam::123456789012:role/mock"
    }
  }

  mock_resource "aws_s3_bucket" {
    defaults = {
      arn = "arn:aws:s3:::mock-bucket"
    }
  }
}

variables {
  alarm_email = ""
}

run "plan_dev" {
  command = plan

  assert {
    condition     = length(module.network.public_subnet_ids) == 2
    error_message = "Expected two public subnets, one per availability zone."
  }

  assert {
    condition     = length(module.observability.alarm_names) == 7
    error_message = "Expected exactly seven CloudWatch alarms."
  }

  assert {
    condition     = module.db.instance_id == "cloudkit-dev-pg"
    error_message = "Expected the RDS instance identifier to be cloudkit-dev-pg."
  }
}

run "alarm_email_subscribes" {
  command = plan

  variables {
    alarm_email = "ops@example.com"
  }

  # With an alarm email set, the count = 1 email subscription must plan cleanly.
  # This run proves that the plan succeeds with the subscription present. Under
  # command = plan the mock provider leaves computed attributes such as the topic
  # ARN unknown, so the assertions use only values known at plan time (configured
  # names and counts).
  assert {
    condition     = module.observability.dashboard_name == "cloudkit-dev"
    error_message = "Expected the dashboard name to be cloudkit-dev when an alarm email is set."
  }

  assert {
    condition     = length(module.observability.alarm_names) == 7
    error_message = "Expected exactly seven CloudWatch alarms when an alarm email is set."
  }
}
