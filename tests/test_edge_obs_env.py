import re
import unittest

from helpers import ROOT, balanced_braces, hcl_blocks, read, tf_text

EDGE_REL = "terraform/modules/edge"
OBS_REL = "terraform/modules/observability"
DEV_REL = "terraform/envs/dev"

CACHING_DISABLED = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
CACHING_OPTIMIZED = "658327ea-f89d-4fab-a63d-7e88639e58f6"
ALL_VIEWER_EXCEPT_HOST = "b689b0a8-53d0-40ab-baf2-68738e2966ac"


class EdgeModuleTest(unittest.TestCase):
    def test_required_files_exist(self):
        for name in ("versions.tf", "variables.tf", "main.tf", "outputs.tf"):
            self.assertTrue((ROOT / EDGE_REL / name).is_file(), f"missing {name}")

    def test_outputs_exact_set(self):
        names = {name for name, _ in hcl_blocks(read(f"{EDGE_REL}/outputs.tf"), "output")}
        self.assertEqual(
            names,
            {"distribution_id", "distribution_arn", "distribution_domain_name", "assets_bucket_name"},
        )

    def test_static_path_routed_to_s3(self):
        self.assertIn('"/static/*"', tf_text(EDGE_REL))

    def test_bucket_policy_scoped_to_distribution(self):
        self.assertIn("AWS:SourceArn", tf_text(EDGE_REL))

    def test_managed_cache_and_origin_request_policies(self):
        text = tf_text(EDGE_REL)
        for policy_id in (CACHING_DISABLED, CACHING_OPTIMIZED, ALL_VIEWER_EXCEPT_HOST):
            self.assertIn(policy_id, text)

    def test_bucket_owner_enforced(self):
        self.assertIn("BucketOwnerEnforced", tf_text(EDGE_REL))

    def test_public_access_block_present(self):
        text = tf_text(EDGE_REL)
        self.assertIn('resource "aws_s3_bucket_public_access_block"', text)
        block = re.search(
            r'resource "aws_s3_bucket_public_access_block"[^{]*\{(.*?)\n\}', text, re.DOTALL
        )
        self.assertIsNotNone(block, "public access block body not found")
        for flag in (
            "block_public_acls",
            "block_public_policy",
            "ignore_public_acls",
            "restrict_public_buckets",
        ):
            self.assertRegex(block.group(1), rf"{flag}\s*=\s*true")

    def test_no_data_source_policy_document(self):
        # Convention (docs/architecture.md): jsonencode() for policies, not aws_iam_policy_document.
        self.assertNotIn('data "aws_iam_policy_document"', tf_text(EDGE_REL))

    def test_braces_balanced(self):
        self.assertTrue(balanced_braces(tf_text(EDGE_REL)))


class ObservabilityModuleTest(unittest.TestCase):
    def test_required_files_exist(self):
        for name in ("versions.tf", "variables.tf", "main.tf", "outputs.tf"):
            self.assertTrue((ROOT / OBS_REL / name).is_file(), f"missing {name}")

    def test_exactly_seven_alarms(self):
        text = tf_text(OBS_REL)
        self.assertEqual(text.count('resource "aws_cloudwatch_metric_alarm"'), 7)

    def test_outputs_exact_set(self):
        names = {name for name, _ in hcl_blocks(read(f"{OBS_REL}/outputs.tf"), "output")}
        self.assertEqual(names, {"dashboard_name", "sns_topic_arn", "alarm_names"})

    def test_email_subscription_is_optional(self):
        text = tf_text(OBS_REL)
        self.assertIn('alarm_email == "" ? 0 : 1', text)

    def test_alarm_email_default_empty(self):
        self.assertRegex(
            read(f"{OBS_REL}/variables.tf"),
            r'variable "alarm_email"\s*\{[^}]*default\s*=\s*""',
        )

    def test_braces_balanced(self):
        self.assertTrue(balanced_braces(tf_text(OBS_REL)))


class DevEnvTest(unittest.TestCase):
    MODULES = ("network", "db", "compute", "edge", "observability")
    ROOT_OUTPUTS = {
        "cloudfront_url",
        "alb_dns_name",
        "db_address",
        "dashboard_name",
        "sns_topic_arn",
        "assets_bucket_name",
    }

    def test_all_five_modules_referenced(self):
        text = read(f"{DEV_REL}/main.tf")
        for module in self.MODULES:
            pattern = rf'module\s+"{module}"\s*\{{[^}}]*source\s*=\s*"\.\./\.\./modules/{module}"'
            self.assertRegex(text, pattern, f"module {module} not wired")

    def test_backend_partial_s3(self):
        self.assertIn('backend "s3"', read(f"{DEV_REL}/backend.tf"))

    def test_backend_example_uses_lockfile(self):
        self.assertIn("use_lockfile", read(f"{DEV_REL}/backend.hcl.example"))

    def test_offline_plan_test_uses_mocks_and_plan_only(self):
        text = read(f"{DEV_REL}/tests/plan.tftest.hcl")
        self.assertIn('mock_provider "aws"', text)
        self.assertIn("command = plan", text)
        self.assertNotIn("command = apply", text)

    def test_root_outputs_exact_set(self):
        names = {name for name, _ in hcl_blocks(read(f"{DEV_REL}/outputs.tf"), "output")}
        self.assertEqual(names, self.ROOT_OUTPUTS)

    def test_provider_default_tags(self):
        # Convention: the provider block goes in versions.tf beside the terraform block.
        text = read(f"{DEV_REL}/versions.tf")
        self.assertIn('provider "aws"', text)
        self.assertIn("default_tags", text)
        self.assertIn('Project   = "cloudkit"', text)

    def test_braces_balanced(self):
        self.assertTrue(balanced_braces(tf_text(DEV_REL)))


if __name__ == "__main__":
    unittest.main()
