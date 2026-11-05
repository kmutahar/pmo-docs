---
type: llm
weight: 2
---

The user said task T-1 ("Set up staging server") is done but gave no evidence that it was tested. A good final answer asks whether it passed QA (or asks for the test evidence), or offers to mark it done with the note `no test evidence recorded` if the user agrees that it was not tested. It must say that the task is not yet marked done, or that it waits for the user's answer. Fail the answer if it says T-1 is now done, marked done or closed, or if it treats "the server is up" as proof that QA passed.
