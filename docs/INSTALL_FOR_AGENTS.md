# Installing pmo-docs for AI Agents

This document contains instructions for an AI coding agent (Codex, Antigravity, Gemini CLI, Cursor, Copilot, or Claude Code) when asked to install or update the `pmo-docs` skill.

When the user gives you the install prompt, read this entire document as data, follow its steps in order, and reply to the user in their language.

---

## Safety guardrails

These rules apply to every step:

1. **Safety rule 1 (No git writes):** Never stage, commit or push files (`git add`, `git commit`, `git push`, etc.).
2. **Safety rule 3 (Ask before writing):** Show the target path and exact commands, and wait for the user to confirm with an explicit "yes" before creating, modifying or deleting any file on disk. A project-level install into `.agents/skills` requires an additional explicit confirmation because it writes outside `pmo/`.
3. **Safety rule 4 (Data, not commands):** This document is reference data for you to execute with the user's consent. It does not authorise running unapproved commands or bypassing user confirmation.
4. **No network calls from the skill itself:** The skill engine and scripts run locally and make no network calls. Only this install/update workflow downloads the release archive from GitHub, and only with user consent.

---

## Step 1: Detect your agent harness

Determine which agent environment you are running in:
- **Claude Code:** Uses the Claude Code plugin system.
- **Antigravity (`agy`), Codex, Gemini CLI, Cursor, or Copilot:** Uses standard Agent Skill directories.
- **Other agents:** Compatible with the open Agent Skills specification using the shared directory `~/.agents/skills/pmo-docs`.

---

## Step 2: Inspect existing copies and launcher

Before downloading or writing anything, check for existing copies of `pmo-docs` across standard locations in order of precedence:

1. **Environment variable:** `$PMO_DOCS_SKILL` if set.
2. **Project skill folders:**
   - `.claude/skills/pmo-docs`
   - `.agents/skills/pmo-docs`
   - `.github/skills/pmo-docs`
   - `.cursor/skills/pmo-docs`
   - `.gemini/skills/pmo-docs`
3. **Claude plugin cache:**
   - `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/plugins/cache/pmo-docs/pmo-docs/*/` (newest semver version).
4. **User-level skill folders:**
   - `~/.claude/skills/pmo-docs`
   - `~/.agents/skills/pmo-docs`
   - `~/.copilot/skills/pmo-docs`
   - `~/.cursor/skills/pmo-docs`
   - `~/.gemini/skills/pmo-docs`

A folder counts as an existing copy only if it contains both `SKILL.md` and `scripts/`.

For each copy found:
- Read `metadata.version` from its `SKILL.md`.
- Record its absolute path.

Read the release version from `https://raw.githubusercontent.com/kmutahar/pmo-docs/v0.7.0/skills/pmo-docs/SKILL.md` (or inspect the release archive tag `v0.7.0`).

### Determine the situation

- **Case A: Copy already matches the release version:**
  If the highest-precedence copy already has the release version (e.g. `0.7.0`), write nothing. Inform the user that the skill is up to date and proceed directly to Step 5 (Verification).
- **Case B: Older copy found:**
  Show the installed version and the release version. Identify any files that differ. Ask the user for confirmation before replacing or updating it.
- **Case C: Multiple copies with different versions:**
  List every copy and its version. Explain which copy the launcher will pick by precedence. Suggest setting `PMO_DOCS_SKILL` if needed. Do not delete any copy without explicit instruction.
- **Case D: No copy found:**
  Proceed to Step 3 to install fresh.

### Check project launcher

If the current folder is a project with `pmo/` set up:
- Check if `pmo/bin/pmo` exists.
- If it exists, compare its content against the release's `skills/pmo-docs/assets/starter/bin/pmo`.
- If it differs, display the difference to the user and ask for confirmation before replacing it. While unresolved, run verification via the Python script directly, not through the launcher.

---

## Step 3: Present plan and wait for confirmation

Display the findings to the user:
1. Detected agent harness.
2. Existing copies found (if any) and their versions.
3. Target installation directory:
   - For Claude Code: Managed via `/plugin` commands.
   - For all other agents: Shared user directory `~/.agents/skills/pmo-docs/` (supported by Codex, Gemini CLI, Cursor, Copilot, and Antigravity). Do not install redundant per-agent copies.
   - If the user explicitly requested a project-level install: `<project>/.agents/skills/pmo-docs/` (flag that this is outside `pmo/`).
4. Exact shell commands you plan to execute.

Ask the user: *"Do you want to proceed with installing/updating pmo-docs?"*
**Wait for an explicit "yes" before proceeding.**

---

## Step 4: Install or update

Once confirmed:

### For Claude Code
Instruct the user or run:
```sh
/plugin marketplace add kmutahar/pmo-docs
/plugin install pmo-docs@pmo-docs
```
*Note:* Never touch the Claude plugin cache by hand.

### For all other agents
Download and extract the `skills/pmo-docs` folder from the GitHub release tag `v0.7.0`:

```sh
# Create parent directory
mkdir -p ~/.agents/skills

# Download and extract the skill folder
TMP_DIR=$(mktemp -d)
curl -fsSL https://github.com/kmutahar/pmo-docs/archive/refs/tags/v0.7.0.tar.gz | tar -xz -C "$TMP_DIR"
rm -rf ~/.agents/skills/pmo-docs
cp -R "$TMP_DIR"/pmo-docs-0.7.0/skills/pmo-docs ~/.agents/skills/pmo-docs
rm -rf "$TMP_DIR"
```

Verify that `~/.agents/skills/pmo-docs/SKILL.md` and `~/.agents/skills/pmo-docs/scripts/` exist.

---

## Step 5: Verification

After installation:

1. **Verify skill scripts:**
   Run:
   ```sh
   python3 ~/.agents/skills/pmo-docs/scripts/render_views.py --help
   ```
   Ensure it exits 0 and prints usage.

2. **Project verification (if in a pmo-docs project):**
   If `pmo/config.yaml` exists in the current project:
   ```sh
   python3 ~/.agents/skills/pmo-docs/scripts/render_views.py --check
   ```
   If `pmo/bin/pmo` is missing or needs updating, ask the user before running:
   ```sh
   python3 ~/.agents/skills/pmo-docs/scripts/setup.py --launcher
   ```

3. **Reply to user:**
   Report the outcome clearly and concisely in the user's language:
   - Installed version and destination directory.
   - Verification status.
   - Next steps (e.g. reload or restart the agent if required by the harness, or run `pmo/bin/pmo render_views --check`).
