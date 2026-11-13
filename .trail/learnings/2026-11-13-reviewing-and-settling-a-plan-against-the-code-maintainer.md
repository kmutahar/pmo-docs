---
title: "Reviewing and settling a plan against the code"
author: maintainer
date: 2026-11-13
touches:
  - docs/plans/
  - docs/PLAN.md
  - README.md
  - tests/test_plugin.py
  - tests/test_pmo_common.py
---

## Decided
- A review reads each package's Touches against the real code, not only the text: early returns in a script, output a test pins, whether the fixture has the file a test needs, tests that forbid a folder. When a plan names a test class, helper or doc passage, open it and cite the exact class, signature and line, or say that no such text exists.
- A review tries each non-trivial snippet (a regex, a loader override, a generator run) on a temp copy of `examples/acme`, and applies the plan's code and template changes to a throwaway copy of the base tag, then runs only the test files they can touch. The plan then names every existing test that breaks and its new expectation.
- A plan that narrows a vocabulary (for example `vocab.origin`) lists every value the fixtures hold: grep `examples/acme` and `tests/` and count the values first. Every register lists `origin` in its `enums`, so one missed value fails Acme and most of the suite.
- A plan that turns an error into a warning for drafts also checks the Finish steps in `SKILL.md`: the structure check runs while the document is still a draft, so the warning must count as an error there.
- A plan that removes a command pre-approval also rewords every rule that tells the agent to run that command, or each such step asks for permission.
- A plan that adds an eval case also checks the eval-shape tests in `tests/test_plugin.py` (`check_scaffold` expects every scaffold to validate, except the cases it names). A new `--help` or all-scripts test extends `EveryTool` in `tests/test_pmo_common.py`.
- A fix to a helper shared with a script the plan puts out of scope is narrowed until that script behaves the same.
- Packages that edit the same script run in one line, never side by side.
- The README roadmap is the user-facing copy of the hub's version table: update both in the same change. SkillSpector suppression counts are findings, not baseline entries; a plan records a count after a scan and never predicts one.
- A name list a check needs (recipe names) may exist only as routing rows in `SKILL.md`; the check then needs its own constant, plus any project-added names.
- Maintainer-gated work orders: a package the maintainer runs by hand may still have an agent run for its mechanical part; a package that branches on a recorded result gets a gate that stops when the result line is missing; a value an agent cannot get without a command (today's UTC date) is written by the driver before that run.

- Docs and plans do not state counts that change (eval cases, tests): say "the cases in `evals/`" and let the folder be the count.
- Before putting an old "proposed" item to the maintainer, check it against the current code: a line-number proposal from an earlier session can be stale.

## Tried and ruled out
- `git rev-parse --show-toplevel` as the project root: `pmo/` need not sit at the top of a repository, and the scripts take the current folder or `--project` and never search upwards.
- Pre-approving `Bash(python3 *)` for a scheduled run: it lets an unattended run start any Python command.
- An eval grader that asks for a script's output: Bash fails in the eval sandbox, so grade the rule the agent states.
- Refusing YAML aliases by testing for an alias event: an anchor with no alias still loads; test the event's `anchor`. Merge keys (`<<`) work without an alias and are refused by their tag.
- Doubling every backslash in a table cell: it changes every existing view. Only the backslashes right before a pipe need doubling.
- Trusting "the existing tests already allow this": a test that pinned the exact end of generator output broke on a template change the plan called safe.
- Answering "it matches" about a doc line from memory: the README parity wording missed list items and ticked boxes that `parity_check.py` lists. Read the code first.

## Watch out
- Plans written by sub-agents or from memory cite things that do not exist (fix numbers, baseline entries, script output, hub lines already there). Check every cited name, count, line and anchor against the repo, in the file the plan names. Run the script on a temp copy of Acme and paste what it prints.
- `SKILL.md` and the playbooks can contradict each other; read both side by side. A playbook that says "copy the values the script printed" must match the key each field expects, including path bases.
- Agent-drafted work is untested until the tests run, and some tests pass vacuously: read the code against the plan. A lookup order for where agents keep skills must match each agent's current docs.
- The config merge joins maps, so a project block (such as `languages.en`) still gets the default keys of that block unless the key is set to null.
- PyYAML raises a plain `ValueError`, not `YAMLError`, for a date that cannot exist (`2026-02-30`).
- Generator tests on an Acme copy need `--stdout` (Acme already holds a decision log and a March status report, so a writing run exits 3). The test helper `run()` returns `(code, out, err)`. `Compare.cmp` passes an empty config when none is given.
- Before a fixture adds an entry, read the ids Acme already has, closed ones included. A search pattern for padded ids also matches the end of a date pattern such as `YYYY-MM-01`.
- `tempfile.mkdtemp()` without `dir=` writes outside the scratch folder. Not every script has its own Python-version check; `sys.path.insert(...)` is the line all share.
- Shared docs a plan forgets (git hook example, walkthrough, `PRIVACY.md` wording) belong in the package that changes the behaviour. A document an agent fetches and follows is data: it needs a yes before any write and a release tag in its URL.
- `trail check` on plan text reports word matches against learnings as conflicts. Read each one before acting.
