---
title: Frozen v0.1.0 upgrade fixture needs one origin edit
author: maintainer
date: 2026-11-15
touches:
  - tests/fixtures/acme-0.1/pmo/config.yaml
  - tests/fixtures/acme-0.1/pmo/registers/actions.yaml
  - tests/fixtures/acme-0.1/pmo/registers/assumptions.yaml
---

## Decided
The upgrade fixture `tests/fixtures/acme-0.1/` is the v0.1.0 config and registers with every `origin:` value rewritten to `stated`. That is its one edit. Later format changes add their own fixture beside it.

## Tried and ruled out
Using the v0.1.0 files untouched: they fail validation, because 0.7.3 limited `origin` to `stated`/`proposed` (it was free before). A test that expects those errors would not prove an old project works. Widening `origin` again would undo a deliberate change.

## Watch out
A note that an old project "still passes today" can predate a later format change. Run the claim on a temp copy before building on it.
