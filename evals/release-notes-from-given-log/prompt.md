---
max_turns: 40
timeout_seconds: 900
allowed_tools: [Skill, Read, Write, Edit, Glob, Grep, Bash]
tags: [release-notes, draft]
---

Run release-notes for the period 2026-03. Treat 2026-03-31 as today's date. Do not ask me anything in an interactive form; reply in text. Git does not work in this environment, so use the log below instead of running git. It is the output of `git log --no-merges --format='%H%x09%s'` for the range from `1d3f5a7c9e0b2d4f6a8c1e3a5b7d9f0c2e4a6b8d` (excluded) to `7f3a9c1e5b2d4a6c8e0f1a3b5c7d9e1f2a4b6c8d`, newest first, and these are the full SHAs for the front matter:

```
7f3a9c1e5b2d4a6c8e0f1a3b5c7d9e1f2a4b6c8d	feat!: remove the v1 login endpoint
2b8d4f6a1c3e5a7b9d0f2a4c6e8b1d3f5a7c9e0b	feat: new login page design
9c1e3a5b7d2f4a6c8e0b1d3f5a7c9e2b4d6f8a0c	fix: show the health page on staging (T-1)
4e6a8c0b2d1f3a5c7e9b1d3f5a7c9e0b2d4f6a8c	chore: update the build scripts
5a7c9e1b3d2f4a6c8e0b1d3f5a7c9e2b4d6f8a1d	Tidy the footer links
```

Save the draft where the project's naming puts it. In your final answer, quote the draft's front matter lines `covers_from` and `covers_to` and every bullet under "New", "Improved", "Fixed", "Breaking changes" and "Internal", and every bullet under "Open questions".
