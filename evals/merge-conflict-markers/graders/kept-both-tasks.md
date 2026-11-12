---
type: llm
weight: 2
---

The agent was asked to fix the tasks register (pmo/registers/tasks.yaml) after a merge left git conflict markers around two new tasks with different titles. A good answer notes that both tasks were kept under the project merge rules, the conflict markers were removed, and that a duplicate id remains for renumber.py. Fail the answer if it kept only one of the tasks, discarded both, failed to remove the conflict markers, or did not mention that the duplicate id remains for renumber.py.
