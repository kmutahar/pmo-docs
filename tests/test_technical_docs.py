"""Tests for technical and domain document templates.
Run from repo root: python3 -m unittest tests.test_technical_docs
"""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TEMPLATES = REPO / "skills/pmo-docs/assets/templates"
SCRIPTS = REPO / "skills/pmo-docs/scripts"
sys.path.insert(0, str(SCRIPTS))
import pmo_common as pc  # noqa: E402
import structure_check as sc  # noqa: E402

CFG = pc.load_config(".", must_exist=False)

TYPES = {  # doc type: (template file, ordered ## headings, generated_from, code_ref)
    "functional-requirements": ("functional-requirements.md", ["Summary", "Requirements", "Quality and constraints", "Out of scope", "Open questions"], ["requirements"], False),
    "test-acceptance": ("test-acceptance.md", ["Scope", "Test environment", "Test cases", "Results", "Requirements coverage", "Acceptance sign-off", "Open questions"], ["tests", "requirements", "environments"], False),
    "defect-gap-report": ("defect-gap-report.md", ["Summary", "Defects", "Open issues", "Gaps", "Recommendations", "Open questions"], ["tests", "issues", "requirements"], False),
    "entity-lifecycle": ("entity-lifecycle.md", ["Entity", "States", "Transitions", "Who can do what", "Rules and side effects", "Gaps", "Open questions"], ["permissions"], True),
    "api-reference": ("api-reference.md", ["Overview", "Authentication and permissions", "Endpoints", "Errors", "Environments", "Open questions"], ["environments", "permissions"], True),
    "integration-guide": ("integration-guide.md", ["Purpose and audience", "Before you start", "Authentication", "Consumers at a glance", "Consumers", "Environments", "Errors and retries", "Go-live checklist", "Open questions"], ["environments", "permissions"], True),
    "architecture-overview": ("architecture-overview.md", ["Context", "Components", "Data and models", "Runtime and environments", "Cross-cutting concerns", "Key decisions", "Open questions"], ["environments", "decisions"], True),
    "user-guide": ("user-guide.md", ["Who this guide is for", "Getting started", "How to", "Roles and what each can do", "Troubleshooting", "Terms", "Open questions"], ["requirements", "permissions"], True),
}

DRAFT_BODIES = {
    "functional-requirements": """# Functional requirements - Acme

## Summary
| ID | Requirement | Priority | Status |
|---|---|---|---|
| REQ-1 | User login | high | verified |

## Requirements
### REQ-1 - User login
- **Priority:** high - **Status:** verified - **Lead:** Alice
- **Description:** User authentication flow
- **Acceptance criteria:** Valid user can sign in
- **Source:** Specification
- **Linked tasks:** T-1

## Quality and constraints
| ID | Requirement | Kind | Acceptance | Status |
|---|---|---|---|---|
| REQ-2 | Response time | quality | Under 200ms | verified |

## Out of scope
- Native mobile login

## Open questions
- None
""",
    "test-acceptance": """# Test acceptance - Acme

**Period:** 2026-03

## Scope
Acceptance testing round for release 1.0.

## Test environment
| ID | Environment | Location | Branch |
|---|---|---|---|
| ENV-1 | Staging | https://staging.example.com | main |

## Test cases
| ID | Test | Kind | Requirement | Expected | Status | Run on |
|---|---|---|---|---|---|---|
| TST-1 | Login test | automated | REQ-1 | Login succeeds | passed | 2026-03-10 |

## Results
**Results:** 1 passed, 0 failed, 0 blocked, 0 not run. 0 skipped.

## Requirements coverage
| Requirement | Title | Tests | Status |
|---|---|---|---|
| REQ-1 | User login | TST-1 | covered |

## Acceptance sign-off
| Role | Name | Decision | Date |
|---|---|---|---|
| QA Lead | Bob | not set | not set |

## Open questions
- None
""",
    "defect-gap-report": """# Defect and gap report - Acme

**Period:** 2026-03

## Summary
**Failed tests:** 1 - **Open issues:** 1 - **Requirements without a passing test:** 1

Quality state summary for current period.

## Defects
| ID | Failed test | Requirement | Issue | Severity | Lead |
|---|---|---|---|---|---|
| TST-2 | Slow query | REQ-2 | I-1 | high | Bob |

## Open issues
| ID | Issue | Severity | Lead | Status | Raised |
|---|---|---|---|---|---|
| I-1 | Slow query on dashboard | high | Bob | open | 2026-03-10 |

## Gaps
| Requirement | Title | Priority | Gap |
|---|---|---|---|
| REQ-2 | Performance | high | test failed |

## Recommendations
- Fix index for issue I-1

## Open questions
- None
""",
    "entity-lifecycle": """# Entity lifecycle - order

## Entity
Order entity description.

**Defined in:** src/models/order.py:10

## States
| State | Meaning | Entered when | Final |
|---|---|---|---|
| draft | Initial state | Created | no |

## Transitions
| From | To | Trigger | Code |
|---|---|---|---|
| draft | paid | pay | src/order.py:45 |

## Who can do what
| Action | Allowed roles | Condition | Source |
|---|---|---|---|
| pay | customer, admin | none | permissions |

## Rules and side effects
- Audit row created at src/order.py:50

## Gaps
- None

## Open questions
- None
""",
    "api-reference": """# API reference - Acme

## Overview
API description.
v1
Bearer token

## Authentication and permissions
| Resource | Action | Allowed roles | Condition |
|---|---|---|---|
| widgets | read | viewer | none |

## Endpoints
### GET /widgets
- **Purpose:** List widgets
- **Access:** viewer
- **Request:** none
- **Response:** list of widgets
- **Errors:** 401 unauthorized
- **Code:** src/routes/widgets.js:10

## Errors
| Status | Meaning | When it happens |
|---|---|---|
| 401 | Unauthorized | Missing token |

## Environments
| Environment | Base address | Notes |
|---|---|---|
| Production | api.example.com | Main live environment |

## Open questions
- None
""",
    "integration-guide": """# Integration guide - Acme

## Purpose and audience
Integration guide for external consumers.

## Before you start
- Request API access
- Node.js 18+
- API_KEY

## Authentication
1. Generate key.
2. Send Authorization header.

## Consumers at a glance
| Consumer | Calls | Auth |
|---|---|---|
| Billing | Invoices API | API key |

## Consumers
### Billing
- **What it calls:** Invoices API
- **Endpoints used:** GET /invoices
- **Roles it needs:** billing-service
- **Differences by environment:** None
- **Failure handling:** Retry 3 times

## Environments
| Environment | Base address | Differences |
|---|---|---|
| Staging | staging.api.example.com | Test keys |

## Errors and retries
| Situation | What the consumer does |
|---|---|
| 503 | Wait 5 seconds and retry |

## Go-live checklist
- [ ] Health check verified

## Open questions
- None
""",
    "architecture-overview": """# Architecture overview - Acme

## Context
Acme project architecture context.

```text
[User] -> [Frontend] -> [Backend API] -> [Database]
```

## Components
| Component | Responsibility | Technology | Location |
|---|---|---|---|
| API Server | Handle HTTP requests | Express | src/server.js:1 |

## Data and models
| Entity | Purpose | Defined in |
|---|---|---|
| Order | Customer order | src/models/order.py:10 |

## Runtime and environments
| Environment | Kind | Location | Deploy |
|---|---|---|---|
| Staging | test | staging.example.com | CI pipeline |

## Cross-cutting concerns
- **Authentication:** JWT tokens checked in src/auth.js:15
- **Configuration:** Environment variables in src/config.js:5
- **Logging:** Structured JSON logging in src/logger.js:10
- **Errors:** Global error middleware in src/errors.js:20

## Key decisions
| ID | Decision | Status |
|---|---|---|
| `DEC-1` | Use Express for API | approved |

## Open questions
- None
""",
    "user-guide": """# User guide - Acme

## Who this guide is for
This guide is for platform users and managers.

## Getting started
1. Open the application.
2. Sign in with your credentials.

## How to
### Create an order
1. Navigate to Orders page.
2. Click New Order and submit.

- **What you see:** Order confirmation with tracking ID
- **Who can do this:** customer, admin

## Roles and what each can do
| Role | Can | Cannot |
|---|---|---|
| customer | Place orders and view history | Modify system settings |

## Troubleshooting
| Problem | Cause | What to do |
|---|---|---|
| Login fails | Invalid password | Reset password via email |

## Terms
| Term | Meaning |
|---|---|
| Order | Request for goods |

## Open questions
- None
""",
}


def build_draft_from_template(doc_type, tpl_path):
    tfm, _ = pc.split_front_matter(pc.read(tpl_path), strict=True)
    dfm = {
        "title": tfm["title"].replace("{{project}}", "Acme").replace("{{entity}}", "order"),
        "type": tfm["type"],
        "project": "Acme",
        "manager": "Alice",
        "template_version": tfm["template_version"],
        "status": "draft",
        "last_updated": "2026-03-15",
    }
    if "period" in tfm:
        dfm["period"] = "2026-03"
    if "code_ref" in tfm:
        dfm["code_ref"] = "abc1234"
    if "checks" in tfm:
        dfm["checks"] = tfm["checks"]

    fm_text = pc.yaml.safe_dump(dfm, sort_keys=False)
    return f"---\n{fm_text}---\n\n{DRAFT_BODIES[doc_type]}"


class TechnicalDocs(unittest.TestCase):
    def test_sections_in_order(self):
        for doc_type, (tpl_file, expected_headings, _, _) in TYPES.items():
            with self.subTest(doc_type):
                tpl_path = TEMPLATES / tpl_file
                self.assertTrue(tpl_path.exists(), f"missing template {tpl_file}")
                _, body = pc.split_front_matter(pc.read(tpl_path), strict=True)
                actual_headings = [title for lv, title, _ in sc.sections(body) if lv == 2]
                self.assertEqual(actual_headings, expected_headings)

    def test_generated_from_matches(self):
        for doc_type, (_, _, expected_generated, _) in TYPES.items():
            with self.subTest(doc_type):
                actual = CFG["doc_types"][doc_type].get("generated_from")
                self.assertEqual(actual, expected_generated)

    def test_code_ref_only_where_named(self):
        for doc_type, (tpl_file, _, _, expected_code_ref) in TYPES.items():
            with self.subTest(doc_type):
                tpl_path = TEMPLATES / tpl_file
                fm, _ = pc.split_front_matter(pc.read(tpl_path), strict=True)
                has_code_ref = "code_ref" in fm
                self.assertEqual(has_code_ref, expected_code_ref, f"{doc_type} code_ref mismatch")
                if has_code_ref:
                    self.assertEqual(fm["code_ref"], "{{commit}}")

    def test_catalogue_text_present(self):
        for doc_type in TYPES:
            with self.subTest(doc_type):
                info = CFG["doc_types"][doc_type]
                when = info.get("when")
                regenerate = info.get("regenerate")
                self.assertIsInstance(when, str)
                self.assertTrue(bool(when.strip()))
                self.assertIsInstance(regenerate, str)
                self.assertTrue(bool(regenerate.strip()))

    def test_where_resolves_each_type(self):
        root = Path(tempfile.mkdtemp()) / "acme"
        try:
            shutil.copytree(REPO / "examples/acme", root)
            for doc_type in TYPES:
                with self.subTest(doc_type):
                    p = subprocess.run(
                        [sys.executable, str(SCRIPTS / "where.py"), doc_type, "2026-03", "--project", str(root)],
                        capture_output=True, text=True, encoding="utf-8"
                    )
                    self.assertEqual(p.returncode, 0, p.stderr)
                    self.assertIn("template_exists: yes", p.stdout)
                    self.assertIn("document: pmo/documents/", p.stdout)
                    info = CFG["doc_types"][doc_type]
                    if "{period}" not in info.get("name", ""):
                        title = info.get("title")
                        self.assertIn(f"document: pmo/documents/{title}.md", p.stdout)
        finally:
            shutil.rmtree(root.parent)

    def test_a_filled_draft_passes_structure_check(self):
        root = Path(tempfile.mkdtemp()) / "acme"
        try:
            shutil.copytree(REPO / "examples/acme", root)
            docs_dir = root / "pmo/documents"
            docs_dir.mkdir(parents=True, exist_ok=True)
            for doc_type, (tpl_file, _, _, _) in TYPES.items():
                with self.subTest(doc_type):
                    draft_content = build_draft_from_template(doc_type, TEMPLATES / tpl_file)
                    doc_path = docs_dir / f"test_{doc_type}.md"
                    doc_path.write_text(draft_content, encoding="utf-8")
                    p = subprocess.run(
                        [sys.executable, str(SCRIPTS / "structure_check.py"), "--project", str(root), str(doc_path)],
                        capture_output=True, text=True, encoding="utf-8"
                    )
                    self.assertEqual(p.returncode, 0, f"{doc_type} failed structure check:\n{p.stdout}\n{p.stderr}")
        finally:
            shutil.rmtree(root.parent)

    def test_a_draft_built_from_the_real_template_body(self):
        # placeholders filled with text, comments kept: reported as a warning; once removed, the draft passes
        for doc_type, (tpl_file, _, _, _) in TYPES.items():
            with self.subTest(doc_type):
                tpl_path = TEMPLATES / tpl_file
                head = build_draft_from_template(doc_type, tpl_path).split("\n---\n", 1)[0] + "\n---\n\n"
                body = re.sub(r"\{\{[^}]*\}\}", "x", pc.split_front_matter(pc.read(tpl_path), strict=True)[1])
                errors, warns = sc.check(REPO / "examples/acme", CFG, head + body)
                self.assertEqual(errors, [], errors)
                self.assertTrue(any("template comments are kept in a draft" in w for w in warns), doc_type)
                clean = re.sub(r"<!--.*?-->\n?", "", body, flags=re.S)
                self.assertEqual(sc.check(REPO / "examples/acme", CFG, head + clean)[0], [], doc_type)

    def test_entity_title_uses_the_entity_placeholder(self):
        tpl_path = TEMPLATES / "entity-lifecycle.md"
        fm, body = pc.split_front_matter(pc.read(tpl_path), strict=True)
        self.assertIn("{{entity}}", fm.get("title", ""))
        h1 = [title for lv, title, _ in sc.sections(body) if lv == 1]
        self.assertEqual(len(h1), 1)
        self.assertIn("{{entity}}", h1[0])

    def test_integration_guide_checks_consumer_sections(self):
        tpl_path = TEMPLATES / "integration-guide.md"
        fm, _ = pc.split_front_matter(pc.read(tpl_path), strict=True)
        checks = fm.get("checks", [])
        lhs = [c for c in checks if c.get("kind") == "listed_have_sections"]
        self.assertEqual(len(lhs), 1)
        self.assertEqual(lhs[0].get("listed_in"), "Consumers at a glance")
        self.assertEqual(lhs[0].get("sections_in"), "Consumers")
        self.assertEqual(lhs[0].get("level"), 3)

    def test_all_eight_types_are_listed(self):
        expected = {
            "functional-requirements",
            "test-acceptance",
            "defect-gap-report",
            "entity-lifecycle",
            "api-reference",
            "integration-guide",
            "architecture-overview",
            "user-guide",
        }
        self.assertEqual(set(TYPES.keys()), expected)


if __name__ == "__main__":
    unittest.main()
