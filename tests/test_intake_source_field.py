"""Tests for intake source fields against config.default.yaml and render_views.py. Run from the repo root: python3 -m unittest tests.test_intake_source_field"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RENDER_VIEWS = REPO / "skills/pmo-docs/scripts/render_views.py"
sys.path.insert(0, str(REPO / "skills/pmo-docs/scripts"))
import pmo_common as pc  # noqa: E402


def run_render(project, *args):
    p = subprocess.run(
        [sys.executable, str(RENDER_VIEWS), "--project", str(project), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return p.returncode, p.stdout + p.stderr


class IntakeSourceField(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "acme"
        shutil.copytree(REPO / "examples/acme", self.root)
        self.reg = self.root / "pmo/registers"

    def tearDown(self):
        shutil.rmtree(self.root.parent)

    def _append_entry(self, path, entry_line):
        existing = path.read_text(encoding="utf-8")
        if existing and not existing.endswith("\n"):
            existing += "\n"
        path.write_text(existing + entry_line, encoding="utf-8")

    def test_source_fields_in_config_are_accepted(self):
        cfg = pc.load_yaml(pc.read(pc.SKILL / "assets" / "config.default.yaml"))
        cases = (
            (
                "tasks",
                "notes",
                '  - {id: T-5, title: Send vendor shortlist, team: web, group: ui, priority: medium, owner: bob, status: not-started, due: 2026-03-25, period: 2026-03, notes: "from chat export, intake 2026-03-16", origin: stated}\n',
            ),
            (
                "actions",
                "source",
                '  - {id: ACT-3, text: Follow up with vendor, owner: bob, due: 2026-03-25, status: open, source: "from chat export, intake 2026-03-16", origin: stated}\n',
            ),
            (
                "decisions",
                "context",
                '  - {id: DEC-3, title: Confirm release window, context: "from chat export, intake 2026-03-16", decision: Keep Thursday releases, options: [Thursday, Friday], consequences: Predictable cadence, decided_by: sam, date: 2026-03-16, status: accepted, supersedes: null, related: [], origin: stated}\n',
            ),
            (
                "risks",
                "description",
                '  - {id: R-3, title: Late vendor reply, description: "from chat export, intake 2026-03-16", probability: medium, impact: high, owner: bob, mitigation: Follow up weekly, status: open, origin: stated, raised: 2026-03-16, closed: null}\n',
            ),
            (
                "issues",
                "description",
                '  - {id: I-5, title: Staging login timeout, description: "from chat export, intake 2026-03-16", severity: medium, owner: alice, status: open, origin: stated, raised: 2026-03-16, resolved: null, related_tasks: []}\n',
            ),
        )
        for register, field, entry_line in cases:
            with self.subTest(register=register, field=field):
                fields = cfg["registers"][register]["fields"]
                self.assertIn(field, fields)
                reg_file = self.reg / cfg["registers"][register]["file"]
                self._append_entry(reg_file, entry_line)
                code, out = run_render(self.root)
                self.assertEqual(code, 0, out)
                code, out = run_render(self.root, "--check")
                self.assertEqual(code, 0, out)

    def test_unknown_source_field_on_task_is_rejected(self):
        tasks_file = self.reg / "tasks.yaml"
        bad_line = '  - {id: T-5, title: Send vendor shortlist, team: web, group: ui, priority: medium, owner: bob, status: not-started, due: 2026-03-25, period: 2026-03, source: "from chat export, intake 2026-03-16", origin: stated}\n'
        self._append_entry(tasks_file, bad_line)
        code, out = run_render(self.root, "--check")
        self.assertEqual(code, 1, out)
        self.assertIn("source", out)


if __name__ == "__main__":
    unittest.main()
