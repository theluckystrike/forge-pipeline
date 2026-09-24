"""Tests for estimate.py. Run with: python3 -m unittest discover -s tests -v"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(ROOT, "estimate.py")
sys.path.insert(0, ROOT)

import estimate  # noqa: E402

AGPL_TEXT = ("                    GNU AFFERO GENERAL PUBLIC LICENSE\n"
             "                       Version 3, 19 November 2007\n")
MIT_TEXT = "MIT License\n\nCopyright (c) 2026 Example\n"


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = "wb" if isinstance(data, bytes) else "w"
    with open(path, mode) as fh:
        fh.write(data)


def run_cli(*args):
    return subprocess.run([sys.executable, SCRIPT] + list(args),
                          capture_output=True, text=True, timeout=60)


class FixtureRepo(unittest.TestCase):
    """A tree with 1,600 bytes of countable source and several things to skip."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="estimate-test-")
        write(os.path.join(self.dir, "app", "main.py"), "x = 1\n" * 100 + "#" * 400)   # 1000 bytes
        write(os.path.join(self.dir, "web", "index.ts"), "let a = 1;\n" * 50 + "/" * 50)  # 600 bytes
        write(os.path.join(self.dir, "node_modules", "left-pad", "index.js"), "a" * 5000)
        write(os.path.join(self.dir, "node_modules", "left-pad", "LICENSE"), "GNU GENERAL PUBLIC LICENSE\n")
        write(os.path.join(self.dir, "dist", "bundle.js"), "b" * 3000)
        write(os.path.join(self.dir, "package-lock.json"), "{}" * 700)
        write(os.path.join(self.dir, "logo.png"), b"\x89PNG\r\n\x1a\n" + b"\0" * 200)
        write(os.path.join(self.dir, "LICENSE"), AGPL_TEXT)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_counts_only_source_bytes(self):
        by_ext, total, skipped = estimate.count_source(self.dir)
        self.assertEqual(total, 1600)
        self.assertEqual(by_ext[".py"], [1, 1000])
        self.assertEqual(by_ext[".ts"], [1, 600])
        self.assertNotIn(".js", by_ext)      # node_modules and dist skipped
        self.assertNotIn(".json", by_ext)    # lockfile skipped
        self.assertNotIn(".png", by_ext)     # image skipped
        self.assertEqual(skipped, 3)         # lockfile, png, LICENSE

    def test_tokens_at_four_bytes(self):
        self.assertEqual(estimate.bytes_to_tokens(1600), 400)

    def test_agpl_license_exits_2(self):
        res = run_cli(self.dir)
        self.assertEqual(res.returncode, 2, res.stdout + res.stderr)
        self.assertIn("WARN copyleft AGPL in LICENSE", res.stdout)
        self.assertIn("source tokens: 400", res.stdout)
        # the GPL LICENSE inside node_modules is an installed dependency, not scanned
        self.assertNotIn("node_modules", res.stdout)

    def test_mit_license_exits_0(self):
        write(os.path.join(self.dir, "LICENSE"), MIT_TEXT)
        res = run_cli(self.dir)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertNotIn("WARN", res.stdout)

    def test_vendored_gpl_is_flagged(self):
        write(os.path.join(self.dir, "LICENSE"), MIT_TEXT)
        write(os.path.join(self.dir, "vendor", "libfoo", "COPYING"),
              "GNU GENERAL PUBLIC LICENSE\nVersion 2, June 1991\n")
        res = run_cli(self.dir)
        self.assertEqual(res.returncode, 2, res.stdout)
        self.assertIn("WARN copyleft GPL in vendor/libfoo/COPYING", res.stdout)

    def test_package_json_license_field(self):
        write(os.path.join(self.dir, "LICENSE"), MIT_TEXT)
        write(os.path.join(self.dir, "package.json"),
              json.dumps({"name": "x", "license": "LGPL-3.0-or-later",
                          "dependencies": {"gpl-thing": "1.0.0"}}))
        findings = estimate.scan_copyleft(self.dir)
        self.assertEqual(findings, [("package.json", ["LGPL"])])

    def test_package_json_dependency_names_are_not_scanned(self):
        write(os.path.join(self.dir, "LICENSE"), MIT_TEXT)
        write(os.path.join(self.dir, "package.json"),
              json.dumps({"name": "x", "license": "MIT",
                          "dependencies": {"gpl-thing": "1.0.0"}}))
        self.assertEqual(estimate.scan_copyleft(self.dir), [])

    def test_pyproject_and_cargo_license_lines(self):
        write(os.path.join(self.dir, "LICENSE"), MIT_TEXT)
        write(os.path.join(self.dir, "pyproject.toml"),
              '[project]\nname = "x"\nlicense = {text = "MPL-2.0"}\n')
        write(os.path.join(self.dir, "crate", "Cargo.toml"),
              '[package]\nname = "y"\nlicense = "EUPL-1.2"\n')
        found = dict(estimate.scan_copyleft(self.dir))
        self.assertEqual(found["pyproject.toml"], ["MPL"])
        self.assertEqual(found[os.path.join("crate", "Cargo.toml")], ["EUPL"])

    def test_source_file_named_license_is_code_not_license(self):
        write(os.path.join(self.dir, "LICENSE"), MIT_TEXT)
        write(os.path.join(self.dir, "app", "license.py"), "# checks GPL headers\n")
        self.assertEqual(estimate.scan_copyleft(self.dir), [])
        by_ext, total, _ = estimate.count_source(self.dir)
        self.assertEqual(by_ext[".py"][0], 2)

    def test_exclude_drops_a_directory(self):
        by_ext, total, _ = estimate.count_source(self.dir, excludes=["web"])
        self.assertEqual(total, 1000)
        self.assertNotIn(".ts", by_ext)
        res = run_cli(self.dir, "--exclude", "web/")
        self.assertIn("source bytes: 1,000", res.stdout)

    def test_not_a_directory_exits_1(self):
        res = run_cli(os.path.join(self.dir, "missing"))
        self.assertEqual(res.returncode, 1)


class PriceTests(unittest.TestCase):
    def test_published_rates(self):
        s, h, t = estimate.price(1_000_000, 500_000)
        self.assertAlmostEqual(s, 100.0)
        self.assertAlmostEqual(h, 20.0)
        self.assertAlmostEqual(t, 120.0)

    def test_custom_rates(self):
        self.assertAlmostEqual(estimate.price(2_000_000, 0, 50, 10)[2], 100.0)


@unittest.skipUnless(shutil.which("git"), "git not installed")
class GitHistoryTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="estimate-git-")
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
                        GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
                        GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
        self.git("init", "-q")
        write(os.path.join(self.dir, "a.py"), "print(1)\n" * 50)
        write(os.path.join(self.dir, "node_modules", "big.js"), "z" * 20000)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "one")

    def git(self, *args):
        subprocess.run(["git", "-C", self.dir] + list(args), check=True,
                       env=self.env, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_history_counted_and_node_modules_excluded(self):
        hb = estimate.git_history_bytes(self.dir)
        self.assertIsNotNone(hb)
        self.assertGreater(hb, 450)      # the a.py patch is in there
        self.assertLess(hb, 20000)       # the node_modules patch is not

    def test_cli_history_flag(self):
        res = run_cli(self.dir, "--history-tokens-from-git")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("history tokens:", res.stdout)

    def test_repo_without_commits_raises(self):
        empty = tempfile.mkdtemp(prefix="estimate-empty-")
        try:
            subprocess.run(["git", "-C", empty, "init", "-q"], check=True, env=self.env)
            with self.assertRaises(RuntimeError):
                estimate.git_history_bytes(empty)
            res = run_cli(empty, "--history-tokens-from-git")
            self.assertIn("history: git log failed", res.stdout)
        finally:
            shutil.rmtree(empty, ignore_errors=True)

    def test_non_git_dir_returns_none(self):
        plain = tempfile.mkdtemp(prefix="estimate-plain-")
        try:
            self.assertIsNone(estimate.git_history_bytes(plain))
        finally:
            shutil.rmtree(plain, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
