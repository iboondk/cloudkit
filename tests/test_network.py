import unittest

from helpers import ROOT, balanced_braces, hcl_blocks, read, tf_text

NET = ROOT / "terraform" / "modules" / "network"
NET_REL = "terraform/modules/network"


class NetworkModuleTest(unittest.TestCase):
    def test_required_files_exist(self):
        for name in ("versions.tf", "variables.tf", "main.tf", "outputs.tf"):
            self.assertTrue((NET / name).is_file(), f"missing {name}")

    def test_outputs_exact_set(self):
        names = {name for name, _ in hcl_blocks(read(f"{NET_REL}/outputs.tf"), "output")}
        self.assertEqual(
            names,
            {
                "vpc_id",
                "public_subnet_ids",
                "private_subnet_ids",
                "alb_security_group_id",
                "app_security_group_id",
                "db_security_group_id",
            },
        )

    def test_variables_present(self):
        names = {name for name, _ in hcl_blocks(read(f"{NET_REL}/variables.tf"), "variable")}
        for required in ("name", "cidr_block", "az_count", "container_port", "tags"):
            self.assertIn(required, names)

    def test_no_nat_or_eip(self):
        text = tf_text(NET_REL)
        self.assertNotIn("aws_nat_gateway", text)
        self.assertNotIn("aws_eip", text)

    def test_cloudfront_prefix_list_and_db_port(self):
        text = tf_text(NET_REL)
        self.assertIn('"com.amazonaws.global.cloudfront.origin-facing"', text)
        self.assertIn("5432", text)

    def test_every_tf_file_has_balanced_braces(self):
        tf_files = sorted((ROOT / "terraform").rglob("*.tf"))
        self.assertTrue(tf_files, "no .tf files found under terraform/")
        for path in tf_files:
            with self.subTest(file=str(path.relative_to(ROOT))):
                self.assertTrue(balanced_braces(path.read_text(encoding="utf-8")))

    def test_versions_pinned(self):
        text = read(f"{NET_REL}/versions.tf")
        self.assertIn(">= 1.10", text)
        self.assertIn("~> 5.80", text)


if __name__ == "__main__":
    unittest.main()
