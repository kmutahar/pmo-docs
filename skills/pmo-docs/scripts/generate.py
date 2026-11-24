#!/usr/bin/env python3
"""Generate a document from templates and registers.

Usage:
    python3 generate.py <type> [period] [--week] [--as-of YYYY-MM-DD] [--subproject ID] [--stdout] [--project ROOT]

--subproject is for a doc type with per_subproject: true: it fills {subproject} in the name and keeps only the register entries whose `subproject` field matches.

Exit codes:
    0 written (or printed with --stdout)
    1 register validation failed
    2 usage, config error, or missing template section
    3 document already exists
"""
import argparse
import calendar
import datetime
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit("pmo-docs needs Python 3.10 or newer (this is %d.%d)." % sys.version_info[:2])

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pmo_common as pc  # noqa: E402
import render_views  # noqa: E402
import docs_audit  # noqa: E402
import snapshot  # noqa: E402

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
    extra: dict[str, str] = field(default_factory=dict)  # '## ' heading text -> a '## ...' block inserted before it; skipped when the template has no such heading


class MissingSection(Exception):
    pass


def majority_month(window) -> str:
    """YYYY-MM holding at least 4 of the window's 7 days (its 4th day), so a week lands in one month whatever the week start."""
    return (window[0] + datetime.timedelta(days=3)).strftime("%Y-%m")


def percent(done, total) -> str:
    """Share done as text: one decimal below 10% (2.8), whole numbers from 10% up, 0 for no tasks or none done."""
    p = round(100 * done / total, 1) if total and done else 0
    return f"{p:.1f}" if 0 < p < 10 else f"{p:.0f}"


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
        m = re.match(r"^[0-9]+", part)
        if m:
            return int(m.group(0))
    return 0


def partition_tasks_by_team(tasks, teams_reg):
    """(teams in order, {team id: [tasks]}, tasks without a known team). A task's team matches a team id or heading, ignoring case."""
    def team_key(tm):
        o = tm.get("order")
        return (o if type(o) in (int, float) else 999, id_number(tm.get("id")))
    teams_sorted = sorted(teams_reg, key=team_key)
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
            d = pc.to_date(due)
            if ctx.window and d and ctx.window[0] <= d <= ctx.window[1]:
                matching.append(t)
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

        if heading_title in filled.extra:
            out_blocks.append(filled.extra[heading_title])

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

        # Untouched section: copy byte for byte, except an empty Open questions list (SKILL.md: write `- None`)
        if heading_title == "Open questions":
            block_text = block_text.replace("- {{question}}", "- None")
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
            f"### {did} - {pc.inline(title)}\n"
            f"- **Status:** {pc.inline(status)} - **Date:** {date_str} - **Decided by:** {pc.inline(decided_by)}\n"
            f"- **Context:** {pc.inline(context)}\n"
            f"- **Decision:** {pc.inline(decision_text)}\n"
            f"- **Options considered:** {pc.inline(opts_str)}\n"
            f"- **Consequences:** {pc.inline(consequences)}\n"
            f"- **Supersedes / related:** {pc.inline(sr_str)}"
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
    pct = percent(done, total)
    blocked = sum(1 for t in tasks if t.get("status") in task_blocked)
    month = majority_month(ctx.window) if ctx.window else ctx.period
    month_title = f"{calendar.month_name[int(month[5:7])]} {month[:4]}"

    # Sort tasks by priority
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

        sorted_group_names = sorted(groups.keys(), key=lambda g: (g == "no group", str(g)))
        lines = [f"## {pc.inline(heading)} - {pc.inline(lead)}"]
        for g in sorted_group_names:
            lines.append(f"\n**{pc.inline(g)}**")
            for t in sorted(groups[g], key=task_sort_key):
                box = "[x]" if t.get("status") in task_done else "[ ]"
                title = t.get("title") or "not recorded"
                tid = t.get("id", "")
                prio = t.get("priority") or "not set"
                due = str(t.get("due")) if t.get("due") else "not set"
                lines.append(f"- {box} {pc.inline(title)} `{tid}` - {pc.inline(prio)} - {due}")

        lines.append(f"\n**Output:** {pc.inline(output_desc)}")
        team_blocks.append("\n".join(lines))

    if no_team_tasks:
        groups = {}
        for t in no_team_tasks:
            g = t.get("group") or "no group"
            groups.setdefault(g, []).append(t)
        sorted_group_names = sorted(groups.keys(), key=lambda g: (g == "no group", str(g)))
        lines = ["## No team - not set"]
        for g in sorted_group_names:
            lines.append(f"\n**{pc.inline(g)}**")
            for t in sorted(groups[g], key=task_sort_key):
                box = "[x]" if t.get("status") in task_done else "[ ]"
                title = t.get("title") or "not recorded"
                tid = t.get("id", "")
                prio = t.get("priority") or "not set"
                due = str(t.get("due")) if t.get("due") else "not set"
                lines.append(f"- {box} {pc.inline(title)} `{tid}` - {pc.inline(prio)} - {due}")
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
        if mp:
            if mp == window_month:
                matching_ms.append(m)
        elif due:
            d = pc.to_date(due)
            if ctx.window and d and ctx.window[0] <= d <= ctx.window[1]:
                matching_ms.append(m)
    matching_ms.sort(key=lambda m: id_number(m.get("id")))

    if matching_ms:
        ms_lines = []
        for m in matching_ms:
            box = "[x]" if m.get("status") in ms_closed else "[ ]"
            title = m.get("title") or "not recorded"
            mid = m.get("id", "")
            ms_lines.append(f"- {box} {pc.inline(title)} `{mid}`")
        ms_body = "\n".join(ms_lines)
    else:
        ms_body = "- None"

    return Filled(
        values={
            "done": str(done),
            "total": str(total),
            "pct": pct,
            "blocked": str(blocked),
            "month": month_title,
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
    goals = sorted(ctx.data.get("goals", []), key=lambda p: id_number(p.get("id")))
    goal_blocks = []
    task_done = pc.statuses(ctx.cfg, "tasks", "done")
    task_dropped = set(pc.statuses(ctx.cfg, "tasks", "closed")) - set(task_done)
    for p in goals:
        pid = p.get("id", "")
        title = p.get("title") or "not recorded"
        objectives = p.get("objectives")
        goal_lines = []
        if isinstance(objectives, (list, tuple)):
            for g in objectives:
                if g:
                    goal_lines.append(f"- {pc.inline(g)}")
        elif objectives:
            goal_lines.append(f"- {pc.inline(objectives)}")
        if not goal_lines:
            goal_lines.append("- not recorded")
        goals_text = "\n".join(goal_lines)

        output = p.get("output") or "not recorded"
        dep_str = format_id_list(p.get("depends_on"))
        owner = pc.person(p.get("owner"), ctx.names)
        acceptance = p.get("acceptance") or "not recorded"
        status = p.get("status") or "not recorded"
        due = str(p.get("due")) if p.get("due") else "not set"
        linked = [t for t in ctx.data.get("tasks", []) if t.get("goal") == pid and t.get("status") not in task_dropped]
        tasks_line = f"**Tasks:** {sum(1 for t in linked if t.get('status') in task_done)} of {len(linked)} done\n" if linked else ""

        block = (
            f"### {pid} - {pc.inline(title)}\n"
            f"{goals_text}\n\n"
            f"**Output:** {pc.inline(output)}\n"
            f"**Depends on:** {dep_str}\n"
            f"**Owner:** {pc.inline(owner)}\n"
            f"{tasks_line}"
            f"**Acceptance criteria:** {pc.inline(acceptance)}\n"
            f"**Status:** {pc.inline(status)} - **Due:** {due}"
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

        sorted_group_names = sorted(groups.keys(), key=lambda g: (g == "no group", str(g)))
        lines = [f"### {pc.inline(heading)} - {pc.inline(lead)}"]
        for g in sorted_group_names:
            lines.append(f"\n**{pc.inline(g)}**")
            for t in sorted(groups[g], key=task_sort_key):
                title = t.get("title") or "not recorded"
                tid = t.get("id", "")
                lines.append(f"- {pc.inline(title)} `{tid}`")
        lines.append(f"\n**Output:** {pc.inline(output_desc)}")
        team_blocks.append("\n".join(lines))

    if no_team_tasks:
        groups = {}
        for t in no_team_tasks:
            g = t.get("group") or "no group"
            groups.setdefault(g, []).append(t)
        sorted_group_names = sorted(groups.keys(), key=lambda g: (g == "no group", str(g)))
        lines = ["### No team - not set"]
        for g in sorted_group_names:
            lines.append(f"\n**{pc.inline(g)}**")
            for t in sorted(groups[g], key=task_sort_key):
                title = t.get("title") or "not recorded"
                tid = t.get("id", "")
                lines.append(f"- {pc.inline(title)} `{tid}`")
        lines.append("\n**Output:** not recorded")
        team_blocks.append("\n".join(lines))

    team_assignments_body = "\n\n".join(team_blocks) if team_blocks else "- None"

    # 4. Dependencies and sequencing
    dep_rows = []
    for p in goals:
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
        asm_lines.append(f"- {pc.inline(txt)} `{aid}`")
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
                d = pc.to_date(due)
                if d and d.strftime("%Y-%m") < window_month:
                    completed_before_count += 1

    all_milestones = ctx.data.get("milestones", [])
    all_issues = ctx.data.get("issues", [])
    all_risks = ctx.data.get("risks", [])

    if ctx.as_of > window[1]:
        def keep_raised(entry):
            d = pc.to_date(entry.get("raised"))
            return d is None or d <= window[1]

        all_issues = [i for i in all_issues if keep_raised(i)]
        all_risks = [r for r in all_risks if keep_raised(r)]

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

    # 2b. Progress by sub-project: only when sub-projects are configured and tasks carry the field
    extra = {}
    if ctx.cfg.get("subprojects") and any(t.get("subproject") for t in counted):
        sp_rows = []
        for sp in [*ctx.cfg["subprojects"], None]:
            sp_tasks = [t for t in counted if (t.get("subproject") or None) == sp]
            if sp_tasks:
                sp_rows.append([sp or "not set", str(sum(1 for t in sp_tasks if t.get("status") not in task_dropped)),
                                str(sum(1 for t in sp_tasks if t.get("status") in task_done)),
                                str(sum(1 for t in sp_tasks if t.get("status") in task_blocked))])
        extra["Completed since last report"] = "## Progress by sub-project\n\n" + pc.md_table(["Sub-project", "Tasks", "Done", "Blocked"], sp_rows).strip()

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
            pn_lines.append(f"- {pc.inline(title)} `{tid}` - {pc.inline(owner)} - {due}")
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

    dec_pending = pc.statuses(ctx.cfg, "decisions", "pending")
    for d in ctx.data.get("decisions", []):
        if d.get("status") in dec_pending:
            did = d.get("id") or "not set"
            item = d.get("title") or d.get("decision") or "not recorded"
            needed_from = pc.person(d.get("decided_by"), ctx.names)
            blocker_rows.append([did, item, needed_from, "not set"])

    change_pending = pc.statuses(ctx.cfg, "changes", "pending")
    for c in ctx.data.get("changes", []):
        if c.get("status") in change_pending:
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

    # 6b. Risks and issues: changes since the last snapshot (all open ones when there is none)
    since, found = snapshot.changes(ctx.root, ctx.cfg, ctx.as_of)
    ri_lines = []
    if since is None:
        ri_lines.append("- No snapshot yet: every open risk and issue is listed.")
        for reg in ("risks", "issues"):
            closed = pc.statuses(ctx.cfg, reg, "closed")
            ri_lines += [f"- {pc.inline(e.get('title') or 'not recorded')} `{e.get('id')}` - {pc.inline(e.get('status') or 'not recorded')}"
                         for e in (all_risks if reg == "risks" else all_issues) if e.get("status") not in closed]
    else:
        for reg in ("risks", "issues"):
            titles = {str(e.get("id")): e.get("title") or "not recorded" for e in ctx.data.get(reg, [])}
            closed = pc.statuses(ctx.cfg, reg, "closed")
            for (kind, r), rows in found.items():
                for i, old, new in rows if r == reg else ():
                    if kind == "added":
                        what = f"added, {pc.inline(new)}"
                    elif kind == "removed":
                        what = "removed from the register"
                    else:
                        what = f"{'closed' if new in closed else 'changed'} ({pc.inline(old)}->{pc.inline(new)})"
                    ri_lines.append(f"- {pc.inline(titles.get(i, 'not recorded'))} `{i}` - {what}")
        if not ri_lines:
            ri_lines.append(f"- No risks or issues added, closed or changed since {since}.")
    risks_issues_body = "\n".join(ri_lines)

    # 7. Notes on data
    notes_on_data_lines = [
        f"- RAG rule: weekly-status; overdue measured at {at}; registers read on {ctx.as_of}.",
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
            "Risks and issues: changes since last report": risks_issues_body,
            "Notes on data": notes_on_data_body,
        },
        slots={},
        notes=notes,
        extra=extra,
    )


def code_list(ids):
    return ", ".join(f"`{x}`" for x in ids) or "none"


def _wbs_key(val):
    if isinstance(val, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", val):
        return tuple(int(p) for p in val.split("."))
    return None


def _group_wbs(group_tasks):
    codes = [t["wbs"] for t in group_tasks if _wbs_key(t.get("wbs")) is not None]
    if not codes:
        return None
    if len(codes) == 1:
        return codes[0]
    parts = [c.split(".") for c in codes]
    prefix = []
    for col in zip(*parts):
        if len(set(col)) == 1:
            prefix.append(col[0])
        else:
            break
    return ".".join(prefix) if prefix else min(codes, key=_wbs_key)


@generator("scope-wbs")
def generate_scope_wbs(ctx: Ctx) -> Filled:
    task_dropped = set(pc.statuses(ctx.cfg, "tasks", "closed")) - set(pc.statuses(ctx.cfg, "tasks", "done"))
    tasks = sorted(
        (t for t in ctx.data.get("tasks", []) if t.get("status") not in task_dropped),
        key=lambda t: (_wbs_key(t.get("wbs")) is None, _wbs_key(t.get("wbs")) or (), id_number(t.get("id"))),
    )
    reqs_of_task = {}
    for r in ctx.data.get("requirements", []):
        rt = r.get("related_tasks") or []
        for tid in rt if isinstance(rt, list) else [rt]:
            reqs_of_task.setdefault(tid, []).append(r.get("id"))

    groups = {}
    for t in tasks:
        groups.setdefault(str(t.get("group") or "no group"), []).append(t)

    group_wbs_map = {g: _group_wbs(ts) for g, ts in groups.items()}
    ordered_groups = sorted(
        groups,
        key=lambda g: (group_wbs_map[g] is None, _wbs_key(group_wbs_map[g]) or (), g == "no group", g),
    )

    rows = []
    for g in ordered_groups:
        ts = groups[g]
        owners = list(dict.fromkeys(pc.person(t.get("owner"), ctx.names) for t in ts if t.get("owner")))
        ids = list(dict.fromkeys([t.get("id") for t in ts] + [r for t in ts for r in reqs_of_task.get(t.get("id"), [])]))
        parts = [
            f"{t['wbs']} {pc.inline(t.get('title') or 'not recorded')}" if _wbs_key(t.get("wbs")) is not None
            else pc.inline(t.get("title") or "not recorded")
            for t in ts
        ]
        rows.append([group_wbs_map[g] or "not set", g, "; ".join(parts),
                     ", ".join(owners) or "not set", "not set", code_list(ids)])

    notes = ["Work breakdown: the Milestone column is not set because tasks carry no milestone link"] if rows else []
    if no_owner := sum(1 for t in tasks if not t.get("owner")):
        notes.append(f"{no_owner} tasks have no owner")

    return Filled(
        values={},
        sections={"Work breakdown": pc.md_table(["WBS", "Deliverable", "Parts", "Owner", "Milestone", "Tasks and requirements"], rows).strip()},
        slots={},
        notes=notes,
    )


@generator("work-order")
def generate_work_order(ctx: Ctx) -> Filled:
    task_closed = pc.statuses(ctx.cfg, "tasks", "closed")
    open_tasks = [t for t in ctx.data.get("tasks", []) if t.get("status") not in task_closed]
    by_person = {}
    for t in open_tasks:
        by_person.setdefault(pc.person(t.get("owner"), ctx.names), []).append(t)

    roster_order = [pc.person(r.get("slug"), ctx.names) for r in ctx.data.get("roster", [])]
    order = [p for p in roster_order if p in by_person]
    order += sorted(p for p in by_person if p not in order and p != "not set") + (["not set"] if "not set" in by_person else [])

    prio_list = ctx.cfg.get("vocab", {}).get("priority_order") or []
    prio_rank = {p: i for i, p in enumerate(prio_list)}

    def task_key(t):
        p = prio_rank.get(t.get("priority"), len(prio_list))
        d = str(t.get("due") or "")
        return (p, not d, d, id_number(t.get("id")))

    # one table (structure_check wants a table directly under `## Tasks`), grouped by person
    rows = [[f"{t.get('title') or 'not recorded'} `{t.get('id', '')}`", p, str(t.get("due") or "not set")]
            for p in order for t in sorted(by_person[p], key=task_key)]

    dues = [str(t["due"]) for t in open_tasks if t.get("due")]
    notes = []
    if missing_due := sum(1 for t in open_tasks if not t.get("due")):
        notes.append(f"{missing_due} open tasks have no due date")

    return Filled(
        values={"lead": pc.inline(", ".join(order)) or "not set", "due date": max(dues) if dues else "not set"},
        sections={"Tasks": pc.md_table(["Task", "Owner", "Due"], rows).strip()},
        slots={},
        notes=notes,
    )


def period_milestones(ctx: Ctx) -> list[dict]:
    """Milestones belonging to the period: its month, or a due date inside the window."""
    window_month = majority_month(ctx.window)
    out = []
    for m in ctx.data.get("milestones", []):
        d = pc.to_date(m.get("due"))
        if (m.get("period") == window_month) if m.get("period") else (d and ctx.window[0] <= d <= ctx.window[1]):
            out.append(m)
    return sorted(out, key=lambda m: (not m.get("due"), str(m.get("due") or ""), id_number(m.get("id"))))


@generator("delivery-report")
def generate_delivery_report(ctx: Ctx) -> Filled:
    counted, notes = period_tasks(ctx)
    task_done = pc.statuses(ctx.cfg, "tasks", "done")
    task_closed = pc.statuses(ctx.cfg, "tasks", "closed")
    delivered = sorted((t for t in counted if t.get("status") in task_done), key=lambda t: id_number(t.get("id")))
    dropped = sum(1 for t in counted if t.get("status") in task_closed and t.get("status") not in task_done)
    carried = sorted((t for t in counted if t.get("status") not in task_closed), key=lambda t: id_number(t.get("id")))
    total = len(counted)
    pct = round(100 * len(delivered) / total) if total else 0

    summary = f"**Planned:** {total} tasks - **Delivered:** {len(delivered)} ({pct}%) - **Dropped:** {dropped} - **Carried over:** {len(carried)}"
    if delivered:
        summary += "\n\n" + "\n".join(
            f"- {pc.inline(t.get('title') or 'not recorded')} `{t.get('id', '')}` - {pc.inline(pc.person(t.get('owner'), ctx.names))} - {t.get('due') or 'not set'}"
            for t in delivered)

    ms_rows = [[m.get("id") or "not set", m.get("title") or "not recorded", str(m.get("due") or "not set"), m.get("status") or "not recorded"]
               for m in period_milestones(ctx)]
    carry_body = "\n".join(f"- {pc.inline(t.get('title') or 'not recorded')} `{t.get('id', '')}`" for t in carried) or "- None"

    return Filled(
        values={},
        sections={
            "Summary": summary,
            "Milestones": pc.md_table(["ID", "Milestone", "Due", "Result"], ms_rows).strip(),
            "Carried to next period": carry_body,
        },
        slots={},
        notes=notes,
    )


@generator("defect-gap-report")
def generate_defect_gap_report(ctx: Ctx) -> Filled:
    issues = {i.get("id"): i for i in ctx.data.get("issues", [])}
    tests = ctx.data.get("tests", [])
    failed = sorted((t for t in tests if t.get("status") == "failed"), key=lambda t: id_number(t.get("id")))
    notes = []

    defect_rows = []
    for t in failed:
        ref = t.get("issue")
        iss = next((issues[i] for i in (ref if isinstance(ref, list) else [ref]) if isinstance(i, (str, int)) and i in issues), None)
        if not iss:
            notes.append(f"failed test {t.get('id')} has no linked issue")
        defect_rows.append([t.get("id") or "not set", t.get("title") or "not recorded", t.get("requirement") or "not recorded",
                            t.get("issue") or "not set", (iss.get("severity") or "not recorded") if iss else "not set",
                            pc.person(t.get("owner"), ctx.names)])

    issue_closed = pc.statuses(ctx.cfg, "issues", "closed")
    sev = ctx.cfg.get("vocab", {}).get("issue_severity") or []  # least severe first
    open_issues = sorted((i for i in issues.values() if i.get("status") not in issue_closed),
                         key=lambda i: (-(sev.index(i["severity"]) if i.get("severity") in sev else -1), id_number(i.get("id"))))
    issue_rows = [[i.get("id") or "not set", i.get("title") or "not recorded", i.get("severity") or "not recorded",
                   pc.person(i.get("owner"), ctx.names), i.get("status") or "not recorded", str(i.get("raised") or "not recorded")]
                  for i in open_issues]

    req_closed = pc.statuses(ctx.cfg, "requirements", "closed")
    gap_rows = []
    for r in sorted(ctx.data.get("requirements", []), key=lambda r: id_number(r.get("id"))):
        if r.get("status") in req_closed:
            continue
        states = {t.get("status") for t in tests if t.get("requirement") == r.get("id")}
        if "passed" in states:
            continue
        gap = "no test" if not states else "test failed" if "failed" in states else "test not run"
        gap_rows.append([r.get("id") or "not set", r.get("title") or "not recorded", r.get("priority") or "not recorded", gap])

    counts = f"**Failed tests:** {len(failed)} - **Open issues:** {len(issue_rows)} - **Requirements without a passing test:** {len(gap_rows)}"
    return Filled(
        values={},
        sections={
            "Summary": counts + "\n\n{{At most three sentences summarizing quality state, critical defects, and release readiness.}}",
            "Defects": pc.md_table(["ID", "Failed test", "Requirement", "Issue", "Severity", "Owner"], defect_rows).strip(),
            "Open issues": pc.md_table(["ID", "Issue", "Severity", "Owner", "Status", "Raised"], issue_rows).strip(),
            "Gaps": pc.md_table(["Requirement", "Title", "Priority", "Gap"], gap_rows).strip(),
        },
        slots={},
        notes=notes,
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    pc.add_project_arg(ap)
    ap.add_argument("type", help="document type (e.g. decision-log)")
    ap.add_argument("period", nargs="?", default=None, help="period string (e.g. 2026-03)")
    ap.add_argument("--week", action="store_true", help="use ISO week as period (YYYY-Www)")
    ap.add_argument("--as-of", type=pc.as_of, default=datetime.date.today(),
                    metavar="YYYY-MM-DD", help="date to evaluate period against (default: today)")
    ap.add_argument("--subproject", metavar="ID", help="for a per_subproject doc type: the sub-project the document is about")
    ap.add_argument("--stdout", action="store_true", help="print document to stdout instead of writing to disk")
    args = ap.parse_args(argv)

    root = Path(args.project).resolve()
    if not root.is_dir():
        ap.error(f"project folder not found: {args.project}")

    cfg = pc.load_config(root)
    draft_lang = pc.languages(cfg)["draft"]
    if draft_lang.split("-")[0] != "en":
        print(f"generators write English only; this project's draft language is {draft_lang}. Set generator: null for each doc type in pmo/config.yaml and draft with references/draft.md.", file=sys.stderr)
        return 2

    doc_types = cfg.get("doc_types", {})
    if args.type not in doc_types:
        ap.error(f"unknown doc type {args.type!r}; known types: {', '.join(sorted(doc_types))}")

    info = doc_types[args.type]
    if info.get("generator") is not True or args.type not in GENERATORS:
        print(f"ERROR doc type `{args.type}` has no generator configured; the agent drafts this document from its template (references/draft.md)", file=sys.stderr)
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

    if bad := render_views.config_errors(cfg, root=root):
        print("\n".join("ERROR " + e for e in bad), file=sys.stderr)
        return 2

    if err := pc.subproject_error(cfg, args.type, args.subproject):
        ap.error(err)

    data, read_errors = render_views.read_registers(root, cfg)
    val_errors = render_views.validate(data, cfg, root=root)
    all_errors = read_errors + val_errors
    if all_errors:
        for err in all_errors:
            print("ERROR", err, file=sys.stderr)
        return 1

    if args.subproject:
        data = pc.for_subproject(cfg, data, args.subproject)

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
        if str(e) == "Risks and issues: changes since last report" and re.search(r"^## Risks and issues[ \t]*$", template_text, re.M):
            print("the template still has the old heading `## Risks and issues`; rename it to `## Risks and issues: changes since last report` (scripts/migrate/0003_status_report_heading.py does it)", file=sys.stderr)
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

    rel_path = pc.doc_rel_path(cfg, args.type, period, args.as_of, subproject=args.subproject)
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
    sys.exit(pc.run(main))
