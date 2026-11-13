#!/usr/bin/env python3
"""Generate a document from templates and registers.

Usage:
    python3 generate.py <type> [period] [--week] [--as-of YYYY-MM-DD] [--stdout] [--project ROOT]

Exit codes:
    0 written (or printed with --stdout)
    1 register validation failed
    2 usage, config error, or missing template section
    3 document already exists
"""
import argparse
import datetime
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit("pmo-docs needs Python 3.10 or newer (this is %d.%d)." % sys.version_info[:2])

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pmo_common as pc  # noqa: E402
import render_views  # noqa: E402
import docs_audit  # noqa: E402

GENERATORS = {}


def generator(doc_type):
    """Decorator that registers fn(ctx) -> Filled."""
    def decorator(fn):
        GENERATORS[doc_type] = fn
        return fn
    return decorator


@dataclass
class Ctx:
    root: Path
    cfg: dict
    doc_type: str
    period: str
    window: tuple[datetime.date, datetime.date] | None
    as_of: datetime.date
    data: dict[str, list[dict]]
    names: dict[str, str]


@dataclass
class Filled:
    values: dict[str, str]      # placeholder -> text, applied to front matter and the text before the first '## '
    sections: dict[str, str]    # exact '## ' heading text -> new body (without the heading line)
    slots: dict[str, str]       # exact '## {{...}}' slot heading text -> the generated '## ...' blocks that replace the slot
    notes: list[str] = field(default_factory=list)  # printed to stderr as 'note: ...' for the agent to put in Open questions


class MissingSection(Exception):
    pass


def majority_month(window) -> str:
    """YYYY-MM holding at least 4 of the window's 7 days (its 4th day), so a week lands in one month whatever the week start."""
    return (window[0] + datetime.timedelta(days=3)).strftime("%Y-%m")


def task_sort_key_for(cfg):
    """Sort key: priority (vocab.priority_order first, unknown last), then due date (unset last), then id number."""
    order = cfg.get("vocab", {}).get("priority_order") or []

    def key(t):
        p, d = t.get("priority"), str(t.get("due") or "")
        return ((p not in order, order.index(p) if p in order else 0, str(p)), not d, d, id_number(t.get("id")))
    return key


def id_number(v):
    s = str(v or "")
    if "-" in s:
        part = s.rsplit("-", 1)[-1]
        m = re.match(r"^\d+", part)
        if m:
            return int(m.group(0))
    return 0


def partition_tasks_by_team(tasks, teams_reg):
    """(teams in order, {team id: [tasks]}, tasks without a known team). A task's team matches a team id or heading, ignoring case."""
    teams_sorted = sorted(teams_reg, key=lambda tm: (tm.get("order") if tm.get("order") is not None else 999, id_number(tm.get("id"))))
    team_tasks = {tm.get("id"): [] for tm in teams_sorted}
    no_team_tasks = []
    for t in tasks:
        raw_team = str(t.get("team") or "").strip().lower()
        tm = next((tm for tm in teams_sorted if raw_team and raw_team in (str(tm.get("id") or "").lower(), str(tm.get("heading") or "").lower())), None)
        (team_tasks[tm.get("id")] if tm else no_team_tasks).append(t)
    return teams_sorted, team_tasks, no_team_tasks


def format_id_list(val):
    if not val:
        return "none"
    if isinstance(val, (list, tuple)):
        items = [str(x) for x in val if x]
    else:
        items = [str(val)]
    if not items:
        return "none"
    return ", ".join(f"`{x}`" for x in items)


def period_tasks(ctx: Ctx) -> tuple[list[dict], list[str]]:
    """Tasks belonging to the period, and notes for tasks without period/due."""
    window_month = majority_month(ctx.window) if ctx.window else ctx.period
    all_tasks = ctx.data.get("tasks", [])
    matching = []
    unassigned = []
    for t in all_tasks:
        p = t.get("period")
        due = t.get("due")
        if p:
            if p == window_month:
                matching.append(t)
        elif due:
            try:
                d = pc.to_date(due)
                if ctx.window and d and ctx.window[0] <= d <= ctx.window[1]:
                    matching.append(t)
            except (ValueError, TypeError):
                unassigned.append(t)
        else:
            unassigned.append(t)

    notes = []
    if unassigned:
        count = len(unassigned)
        sample = [str(t.get("id")) for t in unassigned[:10]]
        more = f", and {count - 10} more" if count > 10 else ""
        notes.append(f"{count} tasks have no period or due date: {', '.join(sample)}{more}")
    return matching, notes


def extract_comments(text: str) -> str:
    """Extract all HTML comment blocks from text, joined by newlines."""
    comments = re.findall(r"<!--.*?-->", text, flags=re.S)
    return "\n\n".join(c.strip() for c in comments)


def fill(template_text: str, filled: Filled) -> str:
    """Apply a Filled to a template. Raises MissingSection(heading) for a section or slot not in the template."""
    m = pc.FRONT_MATTER.match(template_text)
    if not m:
        fm_text = ""
        body = template_text
    else:
        fm_text = m.group(1) or ""
        body = template_text[m.end():]

    # Replace placeholders in front matter text
    for k, v in filled.values.items():
        fv = str(v).replace("\\", "\\\\").replace('"', '\\"')  # the templates put values in double quotes
        fm_text = fm_text.replace(f"{{{{{k}}}}}", fv)
    if "date" in filled.values:
        fm_text = re.sub(r"^last_updated:.*$", f'last_updated: "{filled.values["date"]}"', fm_text, flags=re.M)

    # Split body into blocks at lines starting with '## '
    lines = body.splitlines()
    sec_indices = [i for i, line in enumerate(lines) if line.startswith("## ")]

    if not sec_indices:
        preamble = "\n".join(lines)
        blocks = []
    else:
        preamble = "\n".join(lines[:sec_indices[0]])
        blocks = []
        for idx, start in enumerate(sec_indices):
            end = sec_indices[idx + 1] if idx + 1 < len(sec_indices) else len(lines)
            blocks.append(lines[start:end])

    # Replace placeholders in preamble text
    for k, v in filled.values.items():
        preamble = preamble.replace(f"{{{{{k}}}}}", str(v))

    seen_sections = set()
    seen_slots = set()
    out_blocks = []

    for block_lines in blocks:
        heading_line = block_lines[0]
        heading_title = heading_line[3:].strip()
        block_text = "\n".join(block_lines)
        old_body = "\n".join(block_lines[1:])

        # Check slots first
        slot_key = None
        if heading_title in filled.slots:
            slot_key = heading_title
        elif heading_line in filled.slots:
            slot_key = heading_line

        if slot_key is not None:
            seen_slots.add(slot_key)
            slot_comments = extract_comments(block_text)
            replacement = filled.slots[slot_key].strip()
            if replacement:
                if slot_comments:
                    out_blocks.append(f"{slot_comments}\n\n{replacement}")
                else:
                    out_blocks.append(replacement)
            continue

        # Check sections
        sec_key = None
        if heading_title in filled.sections:
            sec_key = heading_title
        elif heading_line in filled.sections:
            sec_key = heading_line

        if sec_key is not None:
            seen_sections.add(sec_key)
            comments = extract_comments(old_body)
            new_body = filled.sections[sec_key].strip()
            parts = [heading_line]
            if comments:
                parts.append(comments)
            if new_body:
                parts.append(new_body)
            out_blocks.append("\n\n".join(parts))
            continue

        # Untouched section: copy byte for byte
        out_blocks.append(block_text.rstrip("\n"))

    for k in filled.sections:
        if k not in seen_sections:
            raise MissingSection(k)
    for k in filled.slots:
        if k not in seen_slots:
            raise MissingSection(k)

    parts = []
    if fm_text:
        parts.append(f"---\n{fm_text.strip()}\n---")
    if preamble.strip():
        parts.append(preamble.strip())
    parts.extend(b for b in out_blocks if b)

    return "\n\n".join(parts).rstrip("\n") + "\n"


@generator("decision-log")
def generate_decision_log(ctx: Ctx) -> Filled:
    decisions = sorted(ctx.data.get("decisions", []), key=lambda d: id_number(d.get("id")))
    sum_rows = []
    dec_blocks = []

    for d in decisions:
        did = d.get("id", "")
        dec_id_code = f"`{did}`"
        decision_text = d.get("decision") or d.get("title") or "not recorded"
        status = d.get("status") or "not recorded"
        date_str = str(d.get("date")) if d.get("date") else "not set"
        decided_by = pc.person(d.get("decided_by"), ctx.names)
        sum_rows.append([dec_id_code, decision_text, status, date_str, decided_by])

        context = d.get("context") or "not recorded"
        opts = d.get("options")
        if isinstance(opts, (list, tuple)):
            opts_str = ", ".join(str(x) for x in opts) if opts else "not recorded"
        elif opts:
            opts_str = str(opts)
        else:
            opts_str = "not recorded"

        consequences = d.get("consequences") or "not recorded"

        sr_items = []
        for k in ("supersedes", "related"):
            val = d.get(k)
            if isinstance(val, (list, tuple)):
                sr_items.extend(str(x) for x in val if x)
            elif val:
                sr_items.append(str(val))
        sr_str = ", ".join(f"`{x}`" for x in sr_items) if sr_items else "none"

        title = d.get("title") or "not recorded"
        dec_blocks.append(
            f"### {did} - {title}\n"
            f"- **Status:** {status} - **Date:** {date_str} - **Decided by:** {decided_by}\n"
            f"- **Context:** {context}\n"
            f"- **Decision:** {decision_text}\n"
            f"- **Options considered:** {opts_str}\n"
            f"- **Consequences:** {consequences}\n"
            f"- **Supersedes / related:** {sr_str}"
        )

    summary_table = pc.md_table(["ID", "Decision", "Status", "Date", "Decided by"], sum_rows)
    decisions_body = "\n\n".join(dec_blocks)

    return Filled(
        values={},
        sections={
            "Summary": summary_table.strip(),
            "Decisions": decisions_body.strip(),
        },
        slots={},
        notes=[],
    )


@generator("team-checklist")
def generate_team_checklist(ctx: Ctx) -> Filled:
    tasks, notes = period_tasks(ctx)
    task_done = pc.statuses(ctx.cfg, "tasks", "done")
    task_closed = pc.statuses(ctx.cfg, "tasks", "closed")
    task_dropped = set(task_closed) - set(task_done)
    task_blocked = pc.statuses(ctx.cfg, "tasks", "blocked")

    total = sum(1 for t in tasks if t.get("status") not in task_dropped)
    done = sum(1 for t in tasks if t.get("status") in task_done)
    pct = round(100 * done / total) if total else 0
    blocked = sum(1 for t in tasks if t.get("status") in task_blocked)

    # Sort priorities
    task_sort_key = task_sort_key_for(ctx.cfg)

    # Team matching
    teams_sorted, team_tasks, no_team_tasks = partition_tasks_by_team(tasks, ctx.data.get("teams", []))

    # Build slot blocks
    team_blocks = []
    for tm in teams_sorted:
        t_list = team_tasks[tm.get("id")]
        if not t_list:
            continue
        heading = tm.get("heading") or tm.get("id") or "Team"
        lead = pc.person(tm.get("owners"), ctx.names)
        output_desc = tm.get("output") or "not recorded"

        # Groups alphabetical, 'no group' last
        groups = {}
        for t in t_list:
            g = t.get("group") or "no group"
            groups.setdefault(g, []).append(t)

        sorted_group_names = sorted(groups.keys(), key=lambda g: (g == "no group", g))
        lines = [f"## {heading} - {lead}"]
        for g in sorted_group_names:
            lines.append(f"\n**{g}**")
            for t in sorted(groups[g], key=task_sort_key):
                box = "[x]" if t.get("status") in task_done else "[ ]"
                title = t.get("title") or "not recorded"
                tid = t.get("id", "")
                prio = t.get("priority") or "not set"
                due = str(t.get("due")) if t.get("due") else "not set"
                lines.append(f"- {box} {title} `{tid}` - {prio} - {due}")

        lines.append(f"\n**Output:** {output_desc}")
        team_blocks.append("\n".join(lines))

    if no_team_tasks:
        groups = {}
        for t in no_team_tasks:
            g = t.get("group") or "no group"
            groups.setdefault(g, []).append(t)
        sorted_group_names = sorted(groups.keys(), key=lambda g: (g == "no group", g))
        lines = ["## No team - not set"]
        for g in sorted_group_names:
            lines.append(f"\n**{g}**")
            for t in sorted(groups[g], key=task_sort_key):
                box = "[x]" if t.get("status") in task_done else "[ ]"
                title = t.get("title") or "not recorded"
                tid = t.get("id", "")
                prio = t.get("priority") or "not set"
                due = str(t.get("due")) if t.get("due") else "not set"
                lines.append(f"- {box} {title} `{tid}` - {prio} - {due}")
        lines.append("\n**Output:** not recorded")
        team_blocks.append("\n".join(lines))

    # Milestones for End-of-period target check
    window_month = majority_month(ctx.window) if ctx.window else ctx.period
    all_ms = ctx.data.get("milestones", [])
    ms_closed = pc.statuses(ctx.cfg, "milestones", "closed")
    matching_ms = []
    for m in all_ms:
        mp = m.get("period")
        due = m.get("due")
        if mp == window_month:
            matching_ms.append(m)
        elif due:
            try:
                d = pc.to_date(due)
                if ctx.window and d and ctx.window[0] <= d <= ctx.window[1]:
                    matching_ms.append(m)
            except (ValueError, TypeError):
                pass
    matching_ms.sort(key=lambda m: id_number(m.get("id")))

    if matching_ms:
        ms_lines = []
        for m in matching_ms:
            box = "[x]" if m.get("status") in ms_closed else "[ ]"
            title = m.get("title") or "not recorded"
            mid = m.get("id", "")
            ms_lines.append(f"- {box} {title} `{mid}`")
        ms_body = "\n".join(ms_lines)
    else:
        ms_body = "- None"

    return Filled(
        values={
            "done": str(done),
            "total": str(total),
            "pct": str(pct),
            "blocked": str(blocked),
        },
        sections={
            "End-of-period target check": ms_body,
        },
        slots={
            "{{team}} - {{lead}}": "\n\n".join(team_blocks),
        },
        notes=notes,
    )


@generator("project-plan")
def generate_project_plan(ctx: Ctx) -> Filled:
    # 1. Team
    roster = ctx.data.get("roster", [])
    team_rows = []
    for r in roster:
        role = r.get("role") or "not set"
        name = r.get("name") or r.get("slug") or "not set"
        team_rows.append([role, name])
    team_body = pc.md_table(["Role", "Name"], team_rows).strip()

    # 2. Goals
    priorities = sorted(ctx.data.get("priorities", []), key=lambda p: id_number(p.get("id")))
    goal_blocks = []
    for p in priorities:
        pid = p.get("id", "")
        title = p.get("title") or "not recorded"
        goals = p.get("goals")
        goal_lines = []
        if isinstance(goals, (list, tuple)):
            for g in goals:
                if g:
                    goal_lines.append(f"- {g}")
        elif goals:
            goal_lines.append(f"- {goals}")
        if not goal_lines:
            goal_lines.append("- not recorded")
        goals_text = "\n".join(goal_lines)

        output = p.get("output") or "not recorded"
        dep_str = format_id_list(p.get("depends_on"))
        owner = pc.person(p.get("owner"), ctx.names)
        acceptance = p.get("acceptance") or "not recorded"
        status = p.get("status") or "not recorded"
        due = str(p.get("due")) if p.get("due") else "not set"

        block = (
            f"### {pid} - {title}\n"
            f"{goals_text}\n\n"
            f"**Output:** {output}\n"
            f"**Depends on:** {dep_str}\n"
            f"**Owner:** {owner}\n"
            f"**Acceptance criteria:** {acceptance}\n"
            f"**Status:** {status} - **Due:** {due}"
        )
        goal_blocks.append(block)
    goals_body = "\n\n".join(goal_blocks) if goal_blocks else "- None"

    # 3. Team assignments
    task_closed = pc.statuses(ctx.cfg, "tasks", "closed")
    all_tasks = ctx.data.get("tasks", [])
    open_tasks = [t for t in all_tasks if t.get("status") not in task_closed]

    task_sort_key = task_sort_key_for(ctx.cfg)

    teams_sorted, team_tasks, no_team_tasks = partition_tasks_by_team(open_tasks, ctx.data.get("teams", []))

    team_blocks = []
    for tm in teams_sorted:
        t_list = team_tasks[tm.get("id")]
        if not t_list:
            continue
        heading = tm.get("heading") or tm.get("id") or "Team"
        lead = pc.person(tm.get("owners"), ctx.names)
        output_desc = tm.get("output") or "not recorded"

        groups = {}
        for t in t_list:
            g = t.get("group") or "no group"
            groups.setdefault(g, []).append(t)

        sorted_group_names = sorted(groups.keys(), key=lambda g: (g == "no group", g))
        lines = [f"### {heading} - {lead}"]
        for g in sorted_group_names:
            lines.append(f"\n**{g}**")
            for t in sorted(groups[g], key=task_sort_key):
                title = t.get("title") or "not recorded"
                tid = t.get("id", "")
                lines.append(f"- {title} `{tid}`")
        lines.append(f"\n**Output:** {output_desc}")
        team_blocks.append("\n".join(lines))

    if no_team_tasks:
        groups = {}
        for t in no_team_tasks:
            g = t.get("group") or "no group"
            groups.setdefault(g, []).append(t)
        sorted_group_names = sorted(groups.keys(), key=lambda g: (g == "no group", g))
        lines = ["### No team - not set"]
        for g in sorted_group_names:
            lines.append(f"\n**{g}**")
            for t in sorted(groups[g], key=task_sort_key):
                title = t.get("title") or "not recorded"
                tid = t.get("id", "")
                lines.append(f"- {title} `{tid}`")
        lines.append("\n**Output:** not recorded")
        team_blocks.append("\n".join(lines))

    team_assignments_body = "\n\n".join(team_blocks) if team_blocks else "- None"

    # 4. Dependencies and sequencing
    dep_rows = []
    for p in priorities:
        deps = p.get("depends_on")
        blks = p.get("blocks")
        has_deps = bool(deps if isinstance(deps, (list, tuple)) else (deps and str(deps).strip()))
        has_blks = bool(blks if isinstance(blks, (list, tuple)) else (blks and str(blks).strip()))
        if has_deps or has_blks:
            dep_str = format_id_list(deps)
            blk_str = format_id_list(blks)
            pid = p.get("id") or "not set"
            dep_rows.append([pid, dep_str, blk_str])
    dep_table = pc.md_table(["Goal", "Depends on", "Blocks"], dep_rows).strip()

    # 5. Milestones
    milestones = sorted(ctx.data.get("milestones", []), key=lambda m: id_number(m.get("id")))
    ms_rows = []
    for m in milestones:
        mid = m.get("id") or "not set"
        m_title = m.get("title") or "not recorded"
        m_due = str(m.get("due")) if m.get("due") else "not set"
        m_status = m.get("status") or "not recorded"
        ms_rows.append([mid, m_title, m_due, m_status])
    ms_table = pc.md_table(["ID", "Milestone", "Due", "Status"], ms_rows).strip()

    # 6. Risks
    risks_closed = pc.statuses(ctx.cfg, "risks", "closed")
    all_risks = sorted(ctx.data.get("risks", []), key=lambda r: id_number(r.get("id")))
    risk_rows = []
    for r in all_risks:
        if r.get("status") in risks_closed:
            continue
        rid = r.get("id") or "not set"
        rtitle = r.get("title") or "not recorded"
        prob = r.get("probability") or "not set"
        impact = r.get("impact") or "not set"
        owner = pc.person(r.get("owner"), ctx.names)
        mit = r.get("mitigation") or "not recorded"
        risk_rows.append([rid, rtitle, prob, impact, owner, mit])
    risks_table = pc.md_table(["ID", "Risk", "Probability", "Impact", "Owner", "Mitigation"], risk_rows).strip()

    # 7. Assumptions
    assumptions = sorted(ctx.data.get("assumptions", []), key=lambda a: id_number(a.get("id")))
    asm_lines = []
    for a in assumptions:
        txt = a.get("text") or "not recorded"
        aid = a.get("id", "")
        asm_lines.append(f"- {txt} `{aid}`")
    assumptions_body = "\n".join(asm_lines) if asm_lines else "- None"

    # 8. Change log
    changes_accepted = pc.statuses(ctx.cfg, "changes", "accepted")
    all_changes = sorted(ctx.data.get("changes", []), key=lambda c: id_number(c.get("id")))
    change_rows = []
    for c in all_changes:
        if c.get("status") not in changes_accepted:
            continue
        c_date = str(c.get("decided_on") or c.get("date") or "not set")
        c_change = c.get("title") or "not recorded"
        c_decided_by = pc.person(c.get("decided_by"), ctx.names)
        change_rows.append([c_date, c_change, c_decided_by])
    change_log_table = pc.md_table(["Date", "Change", "Decided by"], change_rows).strip()

    # Notes
    missing_due = sum(1 for t in open_tasks if not t.get("due"))
    notes = []
    if missing_due:
        notes.append(f"{missing_due} open tasks have no due date")

    return Filled(
        values={},
        sections={
            "Team": team_body,
            "Goals": goals_body,
            "Team assignments": team_assignments_body,
            "Dependencies and sequencing": dep_table,
            "Milestones": ms_table,
            "Risks": risks_table,
            "Assumptions": assumptions_body,
            "Change log": change_log_table,
        },
        slots={},
        notes=notes,
    )


@generator("status-report")
def generate_status_report(ctx: Ctx) -> Filled:
    w_start_day = pc.week_start(ctx.cfg)
    window = ctx.window or pc.period_range(ctx.period, w_start_day)
    at = min(window[1], ctx.as_of)
    window_month = majority_month(window)

    counted, notes = period_tasks(ctx)
    task_done = pc.statuses(ctx.cfg, "tasks", "done")
    task_closed = pc.statuses(ctx.cfg, "tasks", "closed")
    task_dropped = set(task_closed) - set(task_done)
    task_active = pc.statuses(ctx.cfg, "tasks", "active")
    task_blocked = pc.statuses(ctx.cfg, "tasks", "blocked")

    all_tasks = ctx.data.get("tasks", [])
    completed_before_count = 0
    for t in all_tasks:
        if t.get("status") in task_done:
            p = t.get("period")
            due = t.get("due")
            if p and p < window_month:
                completed_before_count += 1
            elif not p and due:
                try:
                    d = pc.to_date(due)
                    if d and d.strftime("%Y-%m") < window_month:
                        completed_before_count += 1
                except (ValueError, TypeError):
                    pass

    all_milestones = ctx.data.get("milestones", [])
    all_issues = ctx.data.get("issues", [])
    all_risks = ctx.data.get("risks", [])

    rag_color, rag_reason = pc.rag(ctx.cfg, at, counted, all_milestones, all_issues, all_risks)

    total = sum(1 for t in counted if t.get("status") not in task_dropped)
    done = sum(1 for t in counted if t.get("status") in task_done)
    pct = round(100 * done / total) if total else 0

    values = {
        "RAG": rag_color,
        "one-sentence reason": rag_reason,
        "done": str(done),
        "total": str(total),
        "pct": str(pct),
    }

    # 1. Progress by priority
    prio_order = ctx.cfg.get("vocab", {}).get("priority_order") or []
    prio_rows = []
    for level in prio_order:
        lvl_tasks = [t for t in counted if t.get("priority") == level]
        if not lvl_tasks:
            continue
        l_total = sum(1 for t in lvl_tasks if t.get("status") not in task_dropped)
        l_done = sum(1 for t in lvl_tasks if t.get("status") in task_done)
        l_active = sum(1 for t in lvl_tasks if t.get("status") in task_active)
        l_blocked = sum(1 for t in lvl_tasks if t.get("status") in task_blocked)
        l_rag, _ = pc.rag(ctx.cfg, at, lvl_tasks, [], [], [])
        prio_rows.append([level, f"{l_done} / {l_total}", str(l_active), str(l_blocked), l_rag, "{{comment}}"])

    not_set_tasks = [t for t in counted if not t.get("priority") or t.get("priority") not in prio_order]
    if not_set_tasks:
        ns_total = sum(1 for t in not_set_tasks if t.get("status") not in task_dropped)
        ns_done = sum(1 for t in not_set_tasks if t.get("status") in task_done)
        ns_active = sum(1 for t in not_set_tasks if t.get("status") in task_active)
        ns_blocked = sum(1 for t in not_set_tasks if t.get("status") in task_blocked)
        ns_rag, _ = pc.rag(ctx.cfg, at, not_set_tasks, [], [], [])
        prio_rows.append(["not set", f"{ns_done} / {ns_total}", str(ns_active), str(ns_blocked), ns_rag, "{{comment}}"])

    progress_by_priority_body = pc.md_table(["Priority", "Done / Total", "In progress", "Blocked", "RAG", "Comment"], prio_rows).strip()

    # 2. Progress by team
    teams_sorted, team_tasks, no_team_tasks = partition_tasks_by_team(counted, ctx.data.get("teams", []))

    team_rows = []
    for tm in teams_sorted:
        t_list = team_tasks[tm.get("id")]
        if not t_list:
            continue
        heading = tm.get("heading") or tm.get("id") or "Team"
        t_total = sum(1 for t in t_list if t.get("status") not in task_dropped)
        t_done = sum(1 for t in t_list if t.get("status") in task_done)
        t_active = sum(1 for t in t_list if t.get("status") in task_active)
        t_blocked = sum(1 for t in t_list if t.get("status") in task_blocked)
        team_rows.append([heading, f"{t_done} / {t_total}", str(t_active), str(t_blocked), "{{changes}}"])

    if no_team_tasks:
        nt_total = sum(1 for t in no_team_tasks if t.get("status") not in task_dropped)
        nt_done = sum(1 for t in no_team_tasks if t.get("status") in task_done)
        nt_active = sum(1 for t in no_team_tasks if t.get("status") in task_active)
        nt_blocked = sum(1 for t in no_team_tasks if t.get("status") in task_blocked)
        team_rows.append(["No team", f"{nt_done} / {nt_total}", str(nt_active), str(nt_blocked), "{{changes}}"])

    progress_by_team_body = pc.md_table(["Team", "Done / Total", "In progress", "Blocked", "Main changes"], team_rows).strip()

    # 3. Planned next
    unclosed = [t for t in counted if t.get("status") not in task_closed]
    def due_sort_key(t):
        d = t.get("due")
        return (d is None or str(d).strip() == "", str(d or ""), id_number(t.get("id")))

    unclosed_sorted = sorted(unclosed, key=due_sort_key)
    if unclosed_sorted:
        pn_lines = []
        for t in unclosed_sorted:
            title = t.get("title") or "not recorded"
            tid = t.get("id", "")
            owner = pc.person(t.get("owner"), ctx.names)
            due = str(t.get("due")) if t.get("due") else "not set"
            pn_lines.append(f"- {title} `{tid}` - {owner} - {due}")
        planned_next_body = "\n".join(pn_lines)
    else:
        planned_next_body = "- None"

    # 4. Blockers and decisions needed
    blocker_rows = []
    blocked_tasks = [t for t in all_tasks if t.get("status") in task_blocked and t.get("status") not in task_closed]
    for t in blocked_tasks:
        tid = t.get("id") or "not set"
        item = t.get("title") or "not recorded"
        needed_from = pc.person(t.get("owner"), ctx.names)
        by_when = str(t.get("due")) if t.get("due") else "not set"
        blocker_rows.append([tid, item, needed_from, by_when])

    first_dec_status = (ctx.cfg.get("vocab", {}).get("decision_status") or ["proposed"])[0]
    for d in ctx.data.get("decisions", []):
        if d.get("status") == first_dec_status:
            did = d.get("id") or "not set"
            item = d.get("title") or d.get("decision") or "not recorded"
            needed_from = pc.person(d.get("decided_by"), ctx.names)
            blocker_rows.append([did, item, needed_from, "not set"])

    first_change_status = (ctx.cfg.get("vocab", {}).get("change_status") or ["proposed"])[0]
    for c in ctx.data.get("changes", []):
        if c.get("status") == first_change_status:
            cid = c.get("id") or "not set"
            item = c.get("title") or "not recorded"
            needed_from = pc.person(c.get("decided_by"), ctx.names)
            blocker_rows.append([cid, item, needed_from, "not set"])

    blockers_body = pc.md_table(["ID", "Item", "Needed from", "By when"], blocker_rows).strip()

    # 5. Decisions and changes
    w_start, w_end = window
    dc_rows = []
    for d in ctx.data.get("decisions", []):
        dt = pc.to_date(d.get("date"))
        if dt and w_start <= dt <= w_end:
            did = d.get("id") or "not set"
            title = d.get("title") or d.get("decision") or "not recorded"
            st = d.get("status") or "not recorded"
            dc_rows.append((dt, id_number(did), [did, title, st, str(dt)]))

    for c in ctx.data.get("changes", []):
        dt = pc.to_date(c.get("date"))
        if dt and w_start <= dt <= w_end:
            cid = c.get("id") or "not set"
            title = c.get("title") or "not recorded"
            st = c.get("status") or "not recorded"
            dc_rows.append((dt, id_number(cid), [cid, title, st, str(dt)]))

    dc_rows.sort(key=lambda x: (x[0], x[1]))
    decisions_changes_body = pc.md_table(["ID", "Title", "Status", "Date"], [r[2] for r in dc_rows]).strip()

    # 6. Milestones
    ms_closed = pc.statuses(ctx.cfg, "milestones", "closed")
    cutoff_14d = w_end + datetime.timedelta(days=14)
    ms_rows = []
    for m in ctx.data.get("milestones", []):
        mdue = pc.to_date(m.get("due"))
        st = m.get("status")
        include = False
        if st not in ms_closed:
            if mdue and mdue <= cutoff_14d:
                include = True
        else:
            if mdue and w_start <= mdue <= w_end:
                include = True

        if include:
            mid = m.get("id") or "not set"
            title = m.get("title") or "not recorded"
            due_str = str(mdue) if mdue else "not set"
            status_str = st or "not recorded"
            ms_rows.append((mdue is None, mdue, id_number(mid), [mid, title, due_str, status_str]))

    ms_rows.sort(key=lambda x: (x[0], x[1], x[2]))
    milestones_body = pc.md_table(["ID", "Milestone", "Due", "Status"], [r[3] for r in ms_rows]).strip()

    # 7. Notes on data
    notes_on_data_lines = [
        f"- RAG rule: weekly-status, as computed by pmo_common.rag, as of {at}.",
        f"- Tasks counted: period {window_month}; completed before {window_month}: {completed_before_count}.",
        "- No git evidence used.",
    ]
    notes_on_data_body = "\n".join(notes_on_data_lines)

    return Filled(
        values=values,
        sections={
            "Progress by priority": progress_by_priority_body,
            "Progress by team": progress_by_team_body,
            "Planned next": planned_next_body,
            "Blockers and decisions needed": blockers_body,
            "Decisions and changes": decisions_changes_body,
            "Milestones": milestones_body,
            "Notes on data": notes_on_data_body,
        },
        slots={},
        notes=notes,
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Generate a document from templates and registers.")
    pc.add_project_arg(ap)
    ap.add_argument("type", help="document type (e.g. decision-log)")
    ap.add_argument("period", nargs="?", default=None, help="period string (e.g. 2026-03)")
    ap.add_argument("--week", action="store_true", help="use ISO week as period (YYYY-Www)")
    ap.add_argument("--as-of", type=datetime.date.fromisoformat, default=datetime.date.today(),
                    metavar="YYYY-MM-DD", help="date to evaluate period against (default: today)")
    ap.add_argument("--stdout", action="store_true", help="print document to stdout instead of writing to disk")
    args = ap.parse_args(argv)

    root = Path(args.project).resolve()
    if not root.is_dir():
        ap.error(f"project folder not found: {args.project}")

    cfg = pc.load_config(root)
    draft_lang = pc.languages(cfg)["draft"]
    if draft_lang != "en":
        print(f"generators write English only; this project's draft language is {draft_lang}. Set generator: null for each doc type in pmo/config.yaml and draft with references/draft.md.", file=sys.stderr)
        return 2

    doc_types = cfg.get("doc_types", {})
    if args.type not in doc_types:
        ap.error(f"unknown doc type {args.type!r}; known types: {', '.join(sorted(doc_types))}")

    info = doc_types[args.type]
    if info.get("generator") is not True or args.type not in GENERATORS:
        print(f"ERROR doc type `{args.type}` has no generator configured (generator: true)", file=sys.stderr)
        return 2

    try:
        w_start = pc.week_start(cfg)
    except ValueError as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 2

    try:
        period = pc.resolve_period(args.period, args.week, args.as_of, w_start)
    except ValueError as e:
        ap.error(str(e))

    pattern = info.get("name", "{title}.md")
    if "{period}" in pattern or args.period or args.week:
        try:
            window = pc.period_range(period, w_start)
        except ValueError as e:
            ap.error(str(e))
    else:
        month_period = args.as_of.strftime("%Y-%m")
        window = pc.period_range(month_period, w_start)

    if bad := render_views.config_errors(cfg):
        print("\n".join("ERROR " + e for e in bad), file=sys.stderr)
        return 2

    data, read_errors = render_views.read_registers(root, cfg)
    val_errors = render_views.validate(data, cfg, root=root)
    all_errors = read_errors + val_errors
    if all_errors:
        for err in all_errors:
            print("ERROR", err, file=sys.stderr)
        return 1

    tpl_name = info.get("template", f"{args.type}.md")
    try:
        tpl_path, _ = pc.find_asset(root, cfg, "templates", tpl_name)
    except ValueError as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 2
    if not tpl_path.exists():
        print(f"ERROR template {tpl_name} not found", file=sys.stderr)
        return 2

    template_text = pc.read(tpl_path)
    names = pc.roster_names(root, cfg)

    ctx = Ctx(
        root=root,
        cfg=cfg,
        doc_type=args.type,
        period=period,
        window=window,
        as_of=args.as_of,
        data=data,
        names=names,
    )

    gen_fn = GENERATORS[args.type]
    filled = gen_fn(ctx)

    # Standard placeholders
    proj_name = cfg.get("project", {}).get("name") or "not set"
    proj_manager = pc.person(cfg.get("project", {}).get("manager"), names)
    std_values = {
        "project": proj_name,
        "manager": proj_manager,
        "period": period,
        "date": str(args.as_of),
    }
    filled.values = {**std_values, **filled.values}

    try:
        doc_text = fill(template_text, filled)
    except MissingSection as e:
        print(f"ERROR template missing section `{e}` required by generator; set `generator: null` in config to draft manually", file=sys.stderr)
        return 2

    if info.get("generated_from"):
        m = re.match(r"\A---\n(.*?)\n---\n", doc_text, flags=re.S)
        if m:
            fm_text = m.group(1)
            if not re.search(r"^source_hashes:", fm_text, flags=re.M):
                pairs = ", ".join(f'{r}: "{docs_audit.register_hash(root, cfg, r)}"' for r in info["generated_from"] if r in cfg.get("registers", {}))
                hash_line = "source_hashes: {" + pairs + "}"

                def _add_hashes(match):
                    return match.group(0) + "\n" + hash_line

                new_fm = re.sub(r"^status:.*$", _add_hashes, fm_text, count=1, flags=re.M)
                doc_text = "---\n" + new_fm + "\n---\n" + doc_text[m.end():]

    rel_path = pc.doc_rel_path(cfg, args.type, period, args.as_of)
    pc.check_inside(root, rel_path)
    target_path = root / rel_path

    if not args.stdout and target_path.exists():
        print(f"ERROR {rel_path} already exists; edit it, or delete or rename it to regenerate (see draft.md step 2)", file=sys.stderr)
        return 3

    if args.stdout:
        sys.stdout.write(doc_text)
    else:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        pc.safe_write(root, rel_path, doc_text)
        print(f"wrote {rel_path}")

    for note in filled.notes:
        print(f"note: {note}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
