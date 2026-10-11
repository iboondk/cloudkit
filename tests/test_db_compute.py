import re
import unittest

from helpers import ROOT, balanced_braces, hcl_blocks, read, tf_text

DB_REL = "terraform/modules/db"
COMPUTE_REL = "terraform/modules/compute"


class DbModuleTest(unittest.TestCase):
    def test_required_files_exist(self):
        for name in ("versions.tf", "variables.tf", "main.tf", "outputs.tf"):
            self.assertTrue((ROOT / DB_REL / name).is_file(), f"missing {name}")

    def test_outputs_exact_set(self):
        names = {name for name, _ in hcl_blocks(read(f"{DB_REL}/outputs.tf"), "output")}
        self.assertEqual(
            names,
            {"instance_id", "address", "port", "db_name", "master_user_secret_arn"},
        )

    def test_managed_master_password(self):
        text = tf_text(DB_REL)
        self.assertRegex(text, r"manage_master_user_password\s*=\s*true")

    def test_no_password_argument(self):
        # \bpassword\s*= must not match anywhere; manage_master_user_password is
        # excluded by the word boundary because "_" is a word character.
        text = tf_text(DB_REL)
        self.assertIsNone(re.search(r"\bpassword\s*=", text))

    def test_not_publicly_accessible(self):
        self.assertRegex(tf_text(DB_REL), r"publicly_accessible\s*=\s*false")

    def test_storage_encrypted(self):
        self.assertRegex(tf_text(DB_REL), r"storage_encrypted\s*=\s*true")

    def test_instance_class_default(self):
        self.assertIn("db.t4g.micro", tf_text(DB_REL))

    def test_no_data_sources(self):
        text = tf_text(DB_REL)
        self.assertNotIn("aws_iam_policy_document", text)
        self.assertEqual(hcl_blocks(text, "data"), [])

    def test_every_tf_file_has_balanced_braces(self):
        for path in sorted((ROOT / DB_REL).glob("*.tf")):
            with self.subTest(file=path.name):
                self.assertTrue(balanced_braces(path.read_text(encoding="utf-8")))

    def test_versions_identical_to_network(self):
        self.assertEqual(
            read(f"{DB_REL}/versions.tf"),
            read("terraform/modules/network/versions.tf"),
        )


class ComputeModuleTest(unittest.TestCase):
    def test_required_files_exist(self):
        for name in ("versions.tf", "variables.tf", "main.tf", "outputs.tf"):
            self.assertTrue((ROOT / COMPUTE_REL / name).is_file(), f"missing {name}")

    def test_outputs_exact_set(self):
        names = {name for name, _ in hcl_blocks(read(f"{COMPUTE_REL}/outputs.tf"), "output")}
        self.assertEqual(
            names,
            {
                "cluster_name",
                "service_name",
                "alb_dns_name",
                "alb_arn_suffix",
                "target_group_arn_suffix",
                "log_group_name",
                "task_execution_role_arn",
            },
        )

    def test_required_strings_present(self):
        text = tf_text(COMPUTE_REL)
        for needle in (
            "FARGATE",
            "assign_public_ip",
            "AmazonECSTaskExecutionRolePolicy",
            "secretsmanager:GetSecretValue",
            "redis:7-alpine",
            "REDIS_ADDR",
            "APP_ENV",
            "deployment_circuit_breaker",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)

    def test_no_iam_policy_document(self):
        self.assertNotIn("aws_iam_policy_document", tf_text(COMPUTE_REL))

    def test_no_data_sources(self):
        text = tf_text(COMPUTE_REL)
        self.assertNotIn('data "', text)
        self.assertEqual(hcl_blocks(text, "data"), [])

    def test_every_tf_file_has_balanced_braces(self):
        for path in sorted((ROOT / COMPUTE_REL).glob("*.tf")):
            with self.subTest(file=path.name):
                self.assertTrue(balanced_braces(path.read_text(encoding="utf-8")))

    def test_versions_identical_to_network(self):
        self.assertEqual(
            read(f"{COMPUTE_REL}/versions.tf"),
            read("terraform/modules/network/versions.tf"),
        )


if __name__ == "__main__":
    unittest.main()
