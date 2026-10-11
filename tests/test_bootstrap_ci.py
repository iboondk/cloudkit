import re
import unittest

from helpers import ROOT, hcl_blocks, load_yaml, read, tf_text

BOOT_REL = "terraform/bootstrap"
PLAN_WF = ".github/workflows/terraform-plan.yml"
APPLY_WF = ".github/workflows/terraform-apply.yml"
TF_APPLY = "terraform " + "apply"
STATIC_KEY_INPUTS = ("aws-access-key-id", "aws-secret-access-key")
SECRET_PREFIX = "secrets." + "AWS_"

ALLOWED_ACTIONS = {
    "actions/checkout": "v4",
    "hashicorp/setup-terraform": "v3",
    "aws-actions/configure-aws-credentials": "v4",
    "actions/github-script": "v7",
}


def workflow(rel):
    data = load_yaml(rel)
    triggers = data.get("on", data.get(True))
    return data, triggers


class BootstrapTest(unittest.TestCase):
    def test_required_files_exist(self):
        for name in ("versions.tf", "variables.tf", "main.tf", "outputs.tf", "terraform.tfvars.example"):
            self.assertTrue((ROOT / BOOT_REL / name).is_file(), f"missing {name}")

    def test_no_backend_block(self):
        self.assertNotRegex(tf_text(BOOT_REL), r'backend\s+"')

    def test_outputs_exact_set(self):
        names = {name for name, _ in hcl_blocks(read(f"{BOOT_REL}/outputs.tf"), "output")}
        self.assertEqual(
            names,
            {"state_bucket_name", "oidc_provider_arn", "plan_role_arn", "apply_role_arn"},
        )

    def test_github_oidc_provider_trust(self):
        text = tf_text(BOOT_REL)
        self.assertIn("token.actions.githubusercontent.com", text)
        self.assertIn("sts.amazonaws.com", text)

    def test_plan_role_trusts_pull_request_only(self):
        text = tf_text(BOOT_REL)
        self.assertIn(":pull_request", text)

    def test_apply_role_trusts_main_and_production(self):
        text = tf_text(BOOT_REL)
        self.assertIn("ref:refs/heads/main", text)
        self.assertIn("environment:production", text)

    def test_state_bucket_prevent_destroy(self):
        self.assertIn("prevent_destroy = true", tf_text(BOOT_REL))

    def test_state_bucket_denies_insecure_transport(self):
        self.assertIn("aws:SecureTransport", tf_text(BOOT_REL))


class WorkflowTest(unittest.TestCase):
    def setUp(self):
        self.plan, self.plan_on = workflow(PLAN_WF)
        self.apply, self.apply_on = workflow(APPLY_WF)

    def test_plan_triggers_on_pull_request(self):
        self.assertIsInstance(self.plan_on, dict)
        self.assertIn("pull_request", self.plan_on)

    def test_apply_triggers_on_push_to_main(self):
        self.assertIsInstance(self.apply_on, dict)
        self.assertEqual(self.apply_on["push"]["branches"], ["main"])

    def test_id_token_write_permission(self):
        self.assertEqual(self.plan["permissions"]["id-token"], "write")
        self.assertEqual(self.apply["permissions"]["id-token"], "write")

    def test_uses_pinned_allowlisted_actions(self):
        for rel in (PLAN_WF, APPLY_WF):
            text = read(rel)
            for match in re.finditer(r"uses:\s*(\S+)", text):
                ref = match.group(1)
                self.assertIn("@", ref, f"unpinned action {ref} in {rel}")
                name, version = ref.rsplit("@", 1)
                self.assertIn(name, ALLOWED_ACTIONS, f"action {name} not allowlisted in {rel}")
                self.assertEqual(version, ALLOWED_ACTIONS[name], f"wrong pin for {name} in {rel}")

    def test_no_static_aws_keys(self):
        for rel in (PLAN_WF, APPLY_WF):
            text = read(rel)
            for key_input in STATIC_KEY_INPUTS:
                self.assertNotIn(key_input, text, f"{key_input} found in {rel}")
            self.assertNotIn(SECRET_PREFIX, text, f"{SECRET_PREFIX} found in {rel}")

    def test_apply_job_uses_production_environment(self):
        self.assertEqual(self.apply["jobs"]["apply"]["environment"], "production")

    def test_terraform_apply_only_in_apply_workflow(self):
        self.assertIn(TF_APPLY, read(APPLY_WF))
        self.assertNotIn(TF_APPLY, read(PLAN_WF))


if __name__ == "__main__":
    unittest.main()
