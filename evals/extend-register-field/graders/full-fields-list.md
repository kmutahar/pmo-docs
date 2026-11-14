---
type: llm
weight: 3
---

In the project's config a list replaces the skill's default list, so the `registers.tasks.fields` list must hold every default task field plus reviewer: id, title, team, group, priority, owner, status, due, done_on, period, notes, origin, tests, reviewer. The change goes in the project's pmo/config.yaml. A good final answer quotes that full list, shown as a plan awaiting a yes. Fail the answer if the quoted list is only the new field or a shortened list without the default fields, if it names the skill's config.default.yaml as the file to change, or if it says the config was changed.
