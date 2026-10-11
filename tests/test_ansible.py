"""Static checks for the Ansible hardening role (text and YAML only, no ansible needed)."""
import ipaddress
import re
import unittest

from helpers import ROOT, load_yaml, read

ANSIBLE_DIR = ROOT / "ansible"
ROLE_REL = "ansible/roles/hardening"
TASK_FILES = ["preflight.yml", "packages.yml", "ssh.yml", "sysctl.yml", "firewall.yml", "updates.yml", "fail2ban.yml", "auditd.yml"]
MODULE_KEY_RE = re.compile(r"^(ansible\.builtin|ansible\.posix|community\.general)\.")
TASK_KEYWORDS = {
    "name", "when", "loop", "notify", "become", "register", "tags", "vars", "import_tasks",
    "include_tasks", "block", "changed_when", "failed_when", "loop_control", "with_items", "listen",
}
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
DOC_NET = ipaddress.ip_network("203.0.113.0/24")


def task_list(rel_file):
    data = load_yaml(f"{ROLE_REL}/tasks/{rel_file}")
    return data or []


def all_role_tasks():
    tasks = []
    for name in ["main.yml"] + TASK_FILES:
        for task in task_list(name):
            tasks.append((name, task))
    return tasks


class YamlParsesTest(unittest.TestCase):
    def test_every_yml_under_ansible_parses(self):
        paths = sorted(ANSIBLE_DIR.rglob("*.yml"))
        self.assertTrue(paths, "no .yml files found under ansible/")
        for path in paths:
            with self.subTest(file=str(path.relative_to(ROOT))):
                load_yaml(str(path.relative_to(ROOT)))


class PlaybookTest(unittest.TestCase):
    def setUp(self):
        self.plays = load_yaml("ansible/site.yml")

    def test_single_play_targets_all(self):
        self.assertEqual(len(self.plays), 1)
        self.assertEqual(self.plays[0]["hosts"], "all")

    def test_play_becomes_root_and_gathers_facts(self):
        play = self.plays[0]
        self.assertIs(play["become"], True)
        self.assertIs(play["gather_facts"], True)

    def test_play_runs_hardening_role(self):
        roles = self.plays[0]["roles"]
        names = [r if isinstance(r, str) else r.get("role") for r in roles]
        self.assertIn("hardening", names)

    def test_requirements_collections(self):
        reqs = load_yaml("ansible/requirements.yml")
        names = {c["name"] for c in reqs["collections"]}
        self.assertEqual(names, {"ansible.posix", "community.general"})

    def test_requirements_versions_have_upper_bounds(self):
        # An open-ended '>=' lets galaxy resolve a release that needs a newer ansible-core
        # than the role's min_ansible_version, so every range needs both bounds.
        reqs = load_yaml("ansible/requirements.yml")
        for collection in reqs["collections"]:
            with self.subTest(collection=collection["name"]):
                spec = str(collection["version"])
                self.assertRegex(spec, r"^>=\d+\.\d+\.\d+,<\d+\.\d+\.\d+$")

    def test_ansible_cfg_settings(self):
        text = read("ansible/ansible.cfg")
        self.assertIn("roles_path = roles", text)
        self.assertIn("inventory = inventory.example.ini", text)
        self.assertIn("host_key_checking = True", text)
        self.assertIn("retry_files_enabled = False", text)
        self.assertIn("stdout_callback = default", text)


class RoleMetaTest(unittest.TestCase):
    def test_galaxy_info(self):
        meta = load_yaml(f"{ROLE_REL}/meta/main.yml")
        info = meta["galaxy_info"]
        self.assertEqual(info["author"], "iboondk")
        self.assertEqual(info["license"], "MIT")
        self.assertEqual(str(info["min_ansible_version"]), "2.15")
        platforms = {p["name"]: [str(v) for v in p["versions"]] for p in info["platforms"]}
        self.assertEqual(platforms.get("Ubuntu"), ["jammy", "noble"])
        self.assertEqual(platforms.get("Amazon"), ["2023"])
        self.assertEqual(meta["dependencies"], [])


class RoleDefaultsTest(unittest.TestCase):
    def setUp(self):
        self.defaults = load_yaml(f"{ROLE_REL}/defaults/main.yml")

    def test_listed_variables_present(self):
        for key in (
            "hardening_ssh_port",
            "hardening_admin_users",
            "hardening_allow_tcp_ports",
            "hardening_disable_root_login",
            "hardening_password_auth",
            "hardening_auto_updates",
            "hardening_sysctl",
            "hardening_fail2ban",
        ):
            with self.subTest(key=key):
                self.assertIn(key, self.defaults)

    def test_secure_defaults(self):
        self.assertEqual(self.defaults["hardening_ssh_port"], 22)
        self.assertEqual(self.defaults["hardening_admin_users"], [])
        self.assertEqual(self.defaults["hardening_allow_tcp_ports"], [22])
        self.assertIs(self.defaults["hardening_disable_root_login"], True)
        self.assertIs(self.defaults["hardening_password_auth"], False)
        self.assertIs(self.defaults["hardening_auto_updates"], True)
        self.assertIs(self.defaults["hardening_fail2ban"], True)

    def test_sysctl_keys_and_values(self):
        expected = {
            "net.ipv4.conf.all.accept_redirects": 0,
            "net.ipv4.conf.all.send_redirects": 0,
            "net.ipv4.conf.all.rp_filter": 1,
            "net.ipv4.tcp_syncookies": 1,
            "net.ipv4.icmp_echo_ignore_broadcasts": 1,
            "kernel.kptr_restrict": 2,
            "kernel.dmesg_restrict": 1,
            "fs.suid_dumpable": 0,
            "net.ipv6.conf.all.accept_redirects": 0,
        }
        self.assertEqual(self.defaults["hardening_sysctl"], expected)


class RoleTasksStructureTest(unittest.TestCase):
    def test_main_imports_all_task_files(self):
        tasks = task_list("main.yml")
        imported = []
        for task in tasks:
            for key in ("import_tasks", "ansible.builtin.import_tasks"):
                if key in task:
                    imported.append(task[key])
        self.assertEqual(sorted(imported), sorted(TASK_FILES))

    def test_preflight_is_first_import_and_runs_before_any_change(self):
        # Static imports run in file order, so the first imported file is the first task
        # executed. Preflight must be that file, or sshd could move before the guard runs.
        tasks = task_list("main.yml")
        first = tasks[0]
        imported = first.get("import_tasks", first.get("ansible.builtin.import_tasks"))
        self.assertEqual(imported, "preflight.yml")

    def test_first_executed_task_is_the_ssh_port_assert(self):
        first_task = task_list("preflight.yml")[0]
        self.assertIn("ansible.builtin.assert", first_task)
        self.assertEqual(first_task["name"], "Refuse to run if the SSH port would be blocked by the firewall")
        self.assertIn("hardening_allow_tcp_ports", str(first_task["ansible.builtin.assert"]["that"]))

    def test_lockout_and_noble_asserts_only_in_preflight(self):
        # The SSH port guard and the noble guard must not be repeated after the changes they protect.
        guard_markers = ("hardening_ssh_port", "distribution_release", "hardening_allow_tcp_ports")
        for name in TASK_FILES:
            if name == "preflight.yml":
                continue
            for task in task_list(name):
                if "ansible.builtin.assert" not in task:
                    continue
                with self.subTest(file=name, task=task.get("name")):
                    that = str(task["ansible.builtin.assert"].get("that", ""))
                    self.assertFalse(any(marker in that for marker in guard_markers), that)
        preflight_asserts = [t for t in task_list("preflight.yml") if "ansible.builtin.assert" in t]
        self.assertEqual(len(preflight_asserts), 2)

    def test_each_imported_task_file_exists(self):
        for name in TASK_FILES:
            with self.subTest(file=name):
                self.assertTrue((ROOT / ROLE_REL / "tasks" / name).is_file())

    def test_every_task_has_name(self):
        for file_name, task in all_role_tasks():
            with self.subTest(file=file_name, task=task):
                self.assertIsInstance(task, dict)
                self.assertIn("name", task)

    def test_module_keys_are_fully_qualified(self):
        for file_name, task in all_role_tasks():
            module_keys = [k for k in task if k not in TASK_KEYWORDS]
            with self.subTest(file=file_name, task=task.get("name")):
                self.assertEqual(len(module_keys), 1, f"expected one module key, got {module_keys}")
                key = module_keys[0]
                self.assertRegex(key, MODULE_KEY_RE)

    def test_os_branching_present(self):
        for name in ("packages.yml", "firewall.yml", "updates.yml"):
            with self.subTest(file=name):
                text = read(f"{ROLE_REL}/tasks/{name}")
                self.assertIn("ansible_facts['os_family'] == 'Debian'", text)
                self.assertIn("ansible_facts['os_family'] == 'RedHat'", text)

    def test_ssh_task_validates_config(self):
        tasks = task_list("ssh.yml")
        templated = [t for t in tasks if "ansible.builtin.template" in t]
        self.assertEqual(len(templated), 1)
        args = templated[0]["ansible.builtin.template"]
        self.assertIn("validate", args)
        self.assertIn("sshd -t", args["validate"])
        self.assertEqual(args["dest"], "/etc/ssh/sshd_config.d/00-hardening.conf")
        self.assertEqual(args["src"], "00-hardening.conf.j2")
        self.assertEqual(str(args["mode"]), "0600")

    def test_ssh_drop_in_sorts_before_vendor_drop_ins(self):
        # sshd keeps the first value per keyword and reads sshd_config.d in lexical order.
        # 50-cloud-init.conf and 50-redhat.conf must not override the hardening values.
        templated = [t for t in task_list("ssh.yml") if "ansible.builtin.template" in t]
        dest_name = templated[0]["ansible.builtin.template"]["dest"].rsplit("/", 1)[1]
        self.assertEqual(dest_name, "00-hardening.conf")
        self.assertFalse(dest_name.startswith("99-"))

    def test_ssh_verifies_effective_config_with_sshd_t(self):
        text = read(f"{ROLE_REL}/tasks/ssh.yml")
        self.assertIn("/usr/sbin/sshd -T", text)
        self.assertIn("meta: flush_handlers", text)
        for needle in (
            "permitrootlogin ",
            "passwordauthentication ",
            "x11forwarding no",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)

    def test_root_login_assert_accepts_both_prohibit_password_spellings(self):
        # Evaluates the real assert expression with jinja2 and Ansible-equivalent shims for
        # bool, ternary and intersect. This checks the logic, not Ansible's templating engine:
        # `ansible-playbook --syntax-check` remains the authority when ansible is installed.
        try:
            from jinja2 import Environment
        except ImportError:
            self.skipTest("jinja2 not installed")

        assert_task = next(
            t for t in task_list("ssh.yml")
            if "ansible.builtin.assert" in t and str(t.get("name", "")).startswith("Assert effective sshd")
        )
        conditions = [c for c in assert_task["ansible.builtin.assert"]["that"] if "permitrootlogin" in c]
        self.assertEqual(len(conditions), 1)

        env = Environment()
        env.filters["bool"] = lambda v: v if isinstance(v, bool) else str(v).lower() in ("true", "yes", "1", "on")
        env.filters["ternary"] = lambda v, when_true, when_false: when_true if v else when_false
        env.filters["intersect"] = lambda a, b: [x for x in a if x in b]
        template = env.from_string("{{ " + conditions[0] + " }}")

        def passes(disable_root_login, stdout_lines):
            rendered = template.render(
                hardening_disable_root_login=disable_root_login,
                hardening_sshd_effective={"stdout_lines": stdout_lines},
            )
            return rendered == "True"

        cases = [
            # Default branch (disable_root_login true): only 'no' passes.
            (True, ["permitrootlogin no"], True),
            (True, ["permitrootlogin without-password"], False),
            # Non-default branch: sshd -T prints 'without-password' for prohibit-password.
            (False, ["permitrootlogin without-password"], True),
            (False, ["permitrootlogin prohibit-password"], True),
            (False, ["permitrootlogin no"], False),
            (False, ["permitrootlogin yes"], False),
            (False, [], False),
        ]
        for disable_root_login, stdout_lines, expected in cases:
            with self.subTest(disable=disable_root_login, stdout=stdout_lines):
                self.assertIs(passes(disable_root_login, stdout_lines), expected)

    def test_ssh_refuses_nonstandard_port_on_noble_by_default(self):
        text = read(f"{ROLE_REL}/tasks/preflight.yml")
        self.assertIn("distribution_release'] != 'noble'", text)
        self.assertIn("hardening_allow_nonstandard_ssh_port_on_noble", text)
        defaults = load_yaml(f"{ROLE_REL}/defaults/main.yml")
        self.assertIs(defaults["hardening_allow_nonstandard_ssh_port_on_noble"], False)

    def test_sysctl_uses_dict2items(self):
        text = read(f"{ROLE_REL}/tasks/sysctl.yml")
        self.assertIn("dict2items", text)
        self.assertIn("/etc/sysctl.d/99-hardening.conf", text)

    def test_fail2ban_skips_redhat(self):
        self.assertIn("fail2ban is not in the Amazon Linux 2023 base repositories", read(f"{ROLE_REL}/tasks/fail2ban.yml"))

    def test_auditd_rules_watch_expected_files(self):
        text = read(f"{ROLE_REL}/files/hardening.rules")
        for path in ("/etc/passwd", "/etc/shadow", "/etc/sudoers", "/etc/ssh/sshd_config"):
            self.assertIn(f"-w {path} -p wa", text)
        self.assertIn("-k identity", text)
        self.assertIn("-k sshd", text)


class TemplateTest(unittest.TestCase):
    def test_sshd_template_hardening_lines(self):
        text = read(f"{ROLE_REL}/templates/00-hardening.conf.j2")
        self.assertIn("PermitRootLogin no", text)
        self.assertIn("PasswordAuthentication no", text)
        for line in (
            "KbdInteractiveAuthentication no",
            "PubkeyAuthentication yes",
            "X11Forwarding no",
            "MaxAuthTries 3",
            "LoginGraceTime 30",
            "ClientAliveInterval 300",
            "ClientAliveCountMax 2",
            "AllowTcpForwarding no",
        ):
            with self.subTest(line=line):
                self.assertIn(line, text)

    def test_allowusers_is_conditional(self):
        text = read(f"{ROLE_REL}/templates/00-hardening.conf.j2")
        self.assertRegex(text, r"\{%\s*if hardening_admin_users\s*\|\s*length\s*>\s*0\s*%\}\s*\n\s*AllowUsers")


class HandlersTest(unittest.TestCase):
    def test_handler_names_cover_every_notify(self):
        notified = set()
        for _, task in all_role_tasks():
            value = task.get("notify")
            if value is None:
                continue
            if isinstance(value, str):
                notified.add(value)
            else:
                notified.update(value)
        self.assertTrue(notified, "no notify values found in role tasks")
        handlers = load_yaml(f"{ROLE_REL}/handlers/main.yml")
        handler_names = {h["name"] for h in handlers}
        self.assertTrue(notified <= handler_names, f"missing handlers: {notified - handler_names}")
        self.assertIn("restart sshd", handler_names)
        self.assertIn("restart ssh socket", handler_names)
        self.assertIn("restart fail2ban", handler_names)
        self.assertIn("reload auditd", handler_names)


class InventoryTest(unittest.TestCase):
    def test_inventory_has_only_documentation_ips(self):
        text = read("ansible/inventory.example.ini")
        ips = IPV4_RE.findall(text)
        self.assertTrue(ips, "expected at least one example IP")
        for ip in ips:
            with self.subTest(ip=ip):
                self.assertIn(ipaddress.ip_address(ip), DOC_NET)

    def test_inventory_has_bastion_group(self):
        text = read("ansible/inventory.example.ini")
        self.assertIn("[bastion]", text)
        self.assertIn("ansible_user=ubuntu", text)


if __name__ == "__main__":
    unittest.main()
