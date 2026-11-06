---
title: Plans regrouped across versions
author: maintainer
date: 2026-11-06
touches:
  - docs/PLAN.md
  - docs/plans/v0.3.md
  - docs/plans/v0.4.md
  - docs/plans/v0.5.md
  - docs/plans/v1.0.md
---

## Decided
- Work that opens the same code goes into one version, to save agent usage. The version contents are in `docs/PLAN.md` and `docs/plans/`; do not copy them here.
- `schema_version` stays 1 through 1.0.

## Tried and ruled out
- A sub-project config concept (use `release-notes --repo PATH` instead), per-writer id prefixes, a generated config reference, document locks, a migration framework (1.0 uses `renumber.py`).

## Watch out
- v0.3 and v0.4 were written by sub-agents and not read in full; v0.4 W0 checks the v0.2 names against the built code.
