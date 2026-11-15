---
title: Reviewing a plan against the code
author: maintainer
date: 2026-11-15
touches:
  - docs/plans/
  - tests/test_plugin.py
  - tests/test_pmo_common.py
---

## Decided
- Read each package's Touches against the real code, not the text: early returns, output a test pins, fixture files, tests that forbid a folder. Cite the exact class, signature and line, or say no such text exists.
- Try each non-trivial snippet on a temp copy of `examples/acme`, and apply the plan's changes to a throwaway copy of the base tag with the touched tests run. The plan then names every existing test that breaks and its new expectation.
- A plan that narrows a vocabulary lists every value the fixtures hold (grep `examples/acme` and `tests/`): one missed value fails Acme and most of the suite.
- A plan that turns an error into a draft warning also checks the Finish steps in `SKILL.md`. One that removes a command pre-approval rewords every rule telling the agent to run it.
- A plan that adds an eval case checks the eval-shape tests (`check_scaffold` in `tests/test_plugin.py`); a new `--help` or all-scripts test extends `EveryTool` in `tests/test_pmo_common.py`.
- Packages editing the same script run in one line. A fix to a shared helper is narrowed until out-of-scope scripts behave the same.
- The README roadmap and the hub version table change together. Docs and plans give no counts that change (evals, tests); suppression counts are findings, recorded after a scan, never predicted.
- Maintainer-gated work orders: a package that branches on a recorded result stops when the result line is missing; a value an agent cannot get without a command (UTC date) is written by the driver.
- Before putting an old "proposed" item to the maintainer, check it against current code.

## Tried and ruled out
- `git rev-parse --show-toplevel` as the project root: scripts take the cwd or `--project` and never search upwards.
- Pre-approving `Bash(python3 *)` for a scheduled run, and an eval grader that asks for script output.
- Refusing YAML aliases by testing for an alias event: test the event's `anchor`; merge keys (`<<`) are refused by tag.
- Doubling every backslash in a table cell: only backslashes right before a pipe need it.
- Trusting "the existing tests already allow this", or answering "it matches" about a doc line from memory: read the code and run it.

## Watch out
- Plans written by sub-agents or from memory cite things that do not exist (fix numbers, baseline entries, script output). Check every cited name, count and anchor in the named file and paste what the script prints on Acme.
- `SKILL.md` and the playbooks can contradict each other; read both. Agent-drafted work is untested until the tests run, and some pass vacuously.
- The config merge joins maps, so a project block still gets the default keys unless set to null. PyYAML raises a plain `ValueError` for impossible dates (`2026-02-30`).
- Generator tests on an Acme copy need `--stdout` (a writing run exits 3). `run()` returns `(code, out, err)`. Read the ids Acme already holds, closed ones included, before adding an entry.
- `tempfile.mkdtemp()` without `dir=` writes outside the scratch folder; `sys.path.insert(...)` is the one line every script shares.
- Docs a plan forgets (git hook example, walkthrough, `PRIVACY.md`) belong in the package that changes the behaviour. A document an agent fetches and follows needs a yes before any write and a release tag in its URL.
- `trail check` on plan text reports word matches as conflicts: read each.
