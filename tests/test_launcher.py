"""Tests for pmo/bin/pmo launcher. Run from the repo root: python3 -m unittest tests.test_launcher"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LAUNCHER_STARTER = REPO / "skills/pmo-docs/assets/starter/bin/pmo"


def make_fake_skill(path: Path, version: str, script_name: str = "where"):
    path.mkdir(parents=True, exist_ok=True)
    (path / "SKILL.md").write_text(
        f"---\nname: pmo-docs\nmetadata:\n  version: '{version}'\n---\n# Skill\n",
        encoding="utf-8"
    )
    sdir = path / "scripts"
    sdir.mkdir(parents=True, exist_ok=True)
    (path / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (path / ".claude-plugin/plugin.json").write_text(
        f'{{"name": "pmo-docs", "version": "{version}"}}',
        encoding="utf-8"
    )
    (sdir / f"{script_name}.py").write_text(
        f'import sys\nprint("version={version}")\nsys.exit(0)\n',
        encoding="utf-8"
    )
    return path


class Launcher(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.claude = self.tmp / "claude"
        self.claude.mkdir()
        self.proj = self.tmp / "proj"
        self.proj.mkdir()
        self.pmo_bin = self.proj / "pmo/bin"
        self.pmo_bin.mkdir(parents=True)
        self.launcher = self.pmo_bin / "pmo"
        shutil.copyfile(LAUNCHER_STARTER, self.launcher)
        self.launcher.chmod(0o755)

    def run_launcher(self, *args, env=None, cwd=None):
        environ = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(self.home),
            "CLAUDE_CONFIG_DIR": str(self.claude),
        }
        if env:
            environ.update(env)
        p = subprocess.run(
            [str(self.launcher)] + list(args),
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=environ,
            cwd=str(cwd) if cwd else str(self.proj)
        )
        return p.returncode, p.stdout, p.stderr

    def test_precedence(self):
        user_skill = make_fake_skill(self.home / ".claude/skills/pmo-docs", "0.1.0")
        cache_skill = make_fake_skill(self.claude / "plugins/cache/pmo-docs/0.2.0", "0.2.0")
        proj_skill = make_fake_skill(self.proj / ".claude/skills/pmo-docs", "0.3.0")
        env_skill = make_fake_skill(self.tmp / "env_skill", "0.4.0")

        # 1. PMO_DOCS_SKILL wins over everything
        code, out, err = self.run_launcher("where", env={"PMO_DOCS_SKILL": str(env_skill)})
        self.assertEqual(code, 0, err)
        self.assertIn("version=0.4.0", out)

        # 2. Project skill folder wins over cache and user
        code, out, err = self.run_launcher("where")
        self.assertEqual(code, 0, err)
        self.assertIn("version=0.3.0", out)

        # 3. Cache wins over user
        shutil.rmtree(proj_skill)
        code, out, err = self.run_launcher("where")
        self.assertEqual(code, 0, err)
        self.assertIn("version=0.2.0", out)

        # 4. User-level wins when cache is gone
        shutil.rmtree(cache_skill)
        code, out, err = self.run_launcher("where")
        self.assertEqual(code, 0, err)
        self.assertIn("version=0.1.0", out)

    def test_cache_version_choice(self):
        make_fake_skill(self.claude / "plugins/cache/pmo-docs/0.4.0", "0.4.0")
        make_fake_skill(self.claude / "plugins/cache/pmo-docs/0.10.0", "0.10.0")
        code, out, err = self.run_launcher("where")
        self.assertEqual(code, 0, err)
        self.assertIn("version=0.10.0", out)

    def test_nothing_installed_exits_2(self):
        code, out, err = self.run_launcher("where")
        self.assertEqual(code, 2)
        self.assertIn("pmo-docs not found: set PMO_DOCS_SKILL", err)

    def test_acme_render_views_exits_like_script(self):
        acme = self.tmp / "acme"
        shutil.copytree(REPO / "examples/acme", acme)
        launcher = acme / "pmo/bin/pmo"
        launcher.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(LAUNCHER_STARTER, launcher)
        launcher.chmod(0o755)

        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(self.home),
            "PMO_DOCS_SKILL": str(REPO / "skills/pmo-docs"),
        }
        # Initially clean Acme exits 0
        p = subprocess.run([str(launcher), "render_views", "--check"], capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(acme))
        self.assertEqual(p.returncode, 0, p.stderr)

        # Modify a view: render_views --check should exit 1
        with open(acme / "pmo/views/tasks.md", "a", encoding="utf-8") as f:
            f.write("\n<!-- change -->\n")
        p2 = subprocess.run([str(launcher), "render_views", "--check"], capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(acme))
        self.assertEqual(p2.returncode, 1)

    def test_bad_script_name(self):
        skill = make_fake_skill(self.proj / ".claude/skills/pmo-docs", "0.5.0")
        # Script name not matching [a-z_]+
        code, out, err = self.run_launcher("../x")
        self.assertEqual(code, 2)
        self.assertIn("invalid script name", err)
        self.assertIn("available scripts:", err)

        # Script name matching regex but file does not exist
        code, out, err = self.run_launcher("rm")
        self.assertEqual(code, 2)
        self.assertIn("unknown script: rm", err)
        self.assertIn("available scripts:", err)

        # No argument
        code, out, err = self.run_launcher()
        self.assertEqual(code, 2)
        self.assertIn("usage:", err)
        self.assertIn("available scripts:", err)

    def test_invalid_pmo_docs_skill_exits_2(self):
        # Set to nonexistent folder
        code, out, err = self.run_launcher("where", env={"PMO_DOCS_SKILL": str(self.tmp / "nonexistent")})
        self.assertEqual(code, 2)
        self.assertIn("invalid PMO_DOCS_SKILL", err)

        # Set to folder missing SKILL.md and scripts/
        bad_dir = self.tmp / "empty_skill"
        bad_dir.mkdir()
        code, out, err = self.run_launcher("where", env={"PMO_DOCS_SKILL": str(bad_dir)})
        self.assertEqual(code, 2)
        self.assertIn("invalid PMO_DOCS_SKILL", err)

    def test_folder_without_skill_or_scripts_skipped(self):
        # Incomplete project skill folder (has SKILL.md but no scripts/)
        incomplete = self.proj / ".claude/skills/pmo-docs"
        incomplete.mkdir(parents=True)
        (incomplete / "SKILL.md").write_text("# incomplete\n", encoding="utf-8")

        # Valid user-level folder
        make_fake_skill(self.home / ".claude/skills/pmo-docs", "0.1.0")

        code, out, err = self.run_launcher("where")
        self.assertEqual(code, 0, err)
        self.assertIn("version=0.1.0", out)

    def test_launcher_run_from_subfolder_uses_project_root(self):
        skill = make_fake_skill(self.proj / ".claude/skills/pmo-docs", "0.5.0", script_name="inspect_env")
        sdir = skill / "scripts"
        (sdir / "inspect_env.py").write_text(
            'import os, sys, pathlib\n'
            'print("cwd=" + str(pathlib.Path.cwd().resolve()))\n'
            'print("args=" + " ".join(sys.argv[1:]))\n',
            encoding="utf-8"
        )
        subfolder = self.proj / "pmo/registers"
        subfolder.mkdir(parents=True, exist_ok=True)
        code, out, err = self.run_launcher("inspect_env", "--extra", cwd=subfolder)
        self.assertEqual(code, 0, err)
        proj_resolved = str(self.proj.resolve())
        self.assertIn(f"cwd={proj_resolved}", out)
        self.assertIn(f"--project {proj_resolved}", out)
        self.assertIn("--extra", out)

    def test_no_tool_stages_or_commits(self):
        verbs = r"(add|commit|push|restore|rm|reset|checkout|stash|clean)"
        git_literal = re.compile(r"""["']git["']""")
        verb_literal = re.compile(r"""["']""" + verbs + r"""["']""")
        git_words = re.compile(r"\bgit " + verbs + r"\b")

        text = LAUNCHER_STARTER.read_text(encoding="utf-8")
        bad = [
            ln for ln in text.splitlines()
            if git_words.search(ln) or (git_literal.search(ln) and verb_literal.search(ln))
        ]
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
