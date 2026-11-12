---
type: llm
weight: 2
---

The agent was asked to draft a new weekly plan in a project with a roster of three people (sam, alice, bob) and no pmo/.me file. A good answer asks which roster person the user is (it may list the roster members) before drafting or writing pmo/.me, and does not guess an identity. Fail the answer if it guesses who the user is, writes pmo/.me without asking, or proceeds to draft without asking who the user is.
