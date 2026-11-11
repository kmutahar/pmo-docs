# Privacy Policy

Last updated: 2026-11-11 (UTC)

pmo-docs is a project-office and documentation workflow packaged as an Agent Skill. It is a folder of instructions, templates and Python scripts. An AI agent that you run (for example Claude Code) reads the instructions and runs the scripts on your own machine. This page explains what that means for your data.

In short: pmo-docs has no server, no account, no analytics and no network access of its own. It does not collect, send, sell or share anything.

## 1. Who is responsible

pmo-docs is an open-source project maintained by kmutahar. The maintainer does not operate any service for it, so the maintainer never receives your data. The source code is public at <https://github.com/kmutahar/pmo-docs> and you can check every statement on this page against it.

## 2. What data pmo-docs works with

pmo-docs reads and writes only files on your machine:

- **Your `pmo/` folder:** the registers (tasks, risks, decisions, changes and similar), the generated views, `config.yaml` and the documents you create from the templates.
- **Project documents you point it at:** for example when you ask the agent to audit or draft a document.
- **Your project's source code:** when you ask the agent to draft a technical document (API reference, integration guide, architecture overview, user guide, entity lifecycle), it reads routes, data models, permission rules, configuration and test files to cite what they say. It records names (for example variable and setting names), never secret values. It runs read-only git on the project repository (`git rev-parse`, `git log`) to note which commit the code was read at and whether it has moved since. It runs a project command (for example listing the routes of a framework, or starting the app) only after you say yes, and never edits the code.
- **Its own files:** the skill's instructions, templates and default configuration.

These files can contain personal data that you or your team wrote, such as names, email addresses, roles, task owners or meeting notes. pmo-docs does not look for this data, copy it elsewhere (except when you publish, see section 7) or build profiles from it. It only processes it locally so the agent can fill in, check and render your documents.

pmo-docs does not read your browser data, contacts, calendar, mailbox or keychains. Its Python scripts read no environment variables and refuse paths that leave the project folder (absolute paths, `..`, symlinks out of the project and `.git`), with one documented exception: publishing in `repo` mode (writes finished documents into another local repository after confirmation; section 7). Drafting release notes with `--repo` has the agent read the git history of another local repository you name, with read-only `git -C` (allowed in `allowed-tools`). To locate the installed skill without hardcoded paths, the project launcher script (`pmo/bin/pmo`) reads `PMO_DOCS_SKILL`, `HOME` and `CLAUDE_CONFIG_DIR`, searching standard skill folders (`.claude/skills`, `.agents/skills`, `.github/skills`, `.cursor/skills`, `.gemini/skills`, and user-level `~/.claude/skills`, `~/.agents/skills`, `~/.copilot/skills`, `~/.cursor/skills`, `~/.gemini/skills`) and the Claude plugin cache, and reads nothing else.

## 3. What pmo-docs does not do

- **No network calls.** The scripts use only the Python standard library and a vendored copy of PyYAML. They do not open connections, download files, call APIs or send email. The only web addresses in the code are inside comments and documentation text. (When you ask an agent to install or update the skill via `docs/INSTALL_FOR_AGENTS.md`, the agent downloads the release archive from GitHub only after you say yes.)
- **No telemetry or analytics.** Nothing is counted, logged remotely or reported back.
- **No credentials.** It does not read, ask for, store or forward passwords, tokens, API keys or SSH keys.
- **No cookies or tracking.** There is no website or app, so there is nothing to track.
- **No connectors.** It declares no MCP servers and connects to no third-party service.
- **No selling or sharing.** Because the maintainer never receives your data, there is nothing to sell or share.

## 4. Retention and deletion

pmo-docs keeps nothing of its own. It has no database, cache service or log that leaves your machine. The files it writes live in your project, and you keep, move, version or delete them as you choose. To remove everything pmo-docs created, delete the `pmo/` folder (and any generated documents) and uninstall the plugin. There is no remote copy to ask us to erase.

If your project is in a Git repository, your Git history keeps earlier versions of these files according to your own Git settings. That is under your control, not the plugin's.

## 5. Your AI agent and its provider

pmo-docs does not choose where your data goes. When you use it through an AI agent, that agent reads the files it is given and sends the relevant text to its model provider so it can respond. For Claude Code, that is Anthropic and is covered by Anthropic's own terms and privacy policy. Other agents are covered by their providers' policies. This happens whether or not the pmo-docs skill is installed, and it is outside the control of this plugin.

Before you let an agent work on a project, consider what the files contain. Do not put secrets, credentials or data you are not allowed to share with your agent's provider into `pmo/` or into documents you ask it to process.

## 6. Children

pmo-docs is a project-office tool for working professionals. It is not directed at, and not intended for, people under 18. It does not knowingly collect information from anyone, including children.

## 7. Security

All processing happens on your machine under your user account, with the permissions your agent has. The scripts only write inside the project folder (with one exception: publish `repo` mode copies finished documents into another local repository after your explicit confirmation and, after a second yes, commits them there; it never pushes). Automated agent installation guided by `docs/INSTALL_FOR_AGENTS.md` writes the skill folder to `~/.agents/skills` or a project skill folder only after your explicit confirmation. The skill lists the exact commands the agent may run without asking (`allowed-tools` in `skills/pmo-docs/SKILL.md`). You keep control through your agent's own permission prompts. To report a security problem, see "Contact" below.

## 8. Your rights

Because the maintainer holds no data about you, there is nothing to access, correct or delete on a server. Your files stay yours, and you can read, change or delete them at any time. If a law that applies to you gives you additional rights over data, you exercise them against whoever holds the data (your own organisation, or your agent's provider), not against this plugin.

## 9. Changes to this policy

If pmo-docs ever adds a feature that sends data off your machine, this policy will change first and the change will be listed in the release notes (`CHANGELOG.md`). The date at the top shows when this page last changed, and the full history is in the Git log of this repository.

## 10. Contact

For privacy questions or to report a security concern, open an issue at <https://github.com/kmutahar/pmo-docs/issues>. Do not post private data in a public issue; ask for a private way to share details if you need one.
