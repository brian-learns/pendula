# Best & Emerging Practices for Documenting AI Prompts in Coding Projects

*Research synthesis — June 2026*

---

## 1. Prompts as First-Class Artifacts (SPDD)

**Source:** Martin Fowler / Thoughtworks (2026)

Prompts should be **kept in version control alongside code**, not lost in chat histories. The Structured Prompt-Driven Development (SPDD) workflow treats prompts as governed, reviewable, reusable artifacts.

**Key practices:**
- Store prompts in `/.specs/` or `/.prompts/` at repo root
- Each prompt has a REASONS canvas (Requirements, Error handling, Assumptions, Strategy, cONtext, Standards)
- Prompts go through PR review like code
- Version history links prompts to the code they generated

---

## 2. Context Engineering Over Prompt Engineering

**Source:** Packmind / Laurent Py (2026)

The discipline has shifted from *prompt engineering* (crafting a single input) to *context engineering* (building a persistent information environment for all AI interactions).

**Key practices:**
- `/.context/` or `/.specs/` folder with project brief, architecture decisions, coding conventions
- `AGENTS.md` / `HACKERS.md` — shared coding guidelines for AI (and humans)
- `SPEC.md` — living product spec that anchors the agent between sessions
- Context files are versioned and PR-reviewed

---

## 3. The AGENTS.md / HACKERS.md Convention

**Source:** GitHub analysis of 2500+ repos, Addy Osmani, Stack Overflow Blog (2026)

The most widely-adopted emerging practice is a **shared coding guidelines file** read by AI agents at the start of every session.

**GitHub's six recommended sections** (from their analysis of effective agent configs):

| Section | What to include |
|---------|----------------|
| Commands | Exact CLI commands: `npm test`, `pytest -v`, `npm run build` |
| Testing | Framework, test location, coverage expectations |
| Project structure | Where source/tests/docs live |
| Code style | One real code snippet beats three paragraphs |
| Git workflow | Branch naming, commit format, PR conventions |
| Boundaries | What the agent must never touch (secrets, vendor dirs, prod configs) |

**Pendula already has this:** `HACKERS.md` covers architecture, style, testing, tools pattern, logging, safety, git workflow.

---

## 4. Spec-Driven Development

**Source:** Addy Osmani, GitHub Spec Kit (2026)

Start with a **high-level spec**, let the AI expand it into a detailed plan, then execute. The spec becomes the source of truth.

**Workflow:**
1. Write a concise product brief (what & why, not how)
2. Let the AI draft a detailed `SPEC.md`
3. Review and refine in **Plan Mode** (read-only)
4. Execute with spec as context
5. Iterate

---

## 5. Prompt Libraries & Templates

**Source:** Multiple (2025-2026)

Teams are building **shared prompt libraries** for common tasks (code review, refactoring, test generation, security audit). These are stored in-repo and reused across sessions.

**Emerging patterns:**
- `/.prompts/review.md` — code review prompt template
- `/.prompts/refactor.md` — refactoring prompt with conventions
- `/.prompts/security.md` — security audit prompt
- Prompts use CRTSE framework (Context, Role, Task, Structure, Examples)

---

## 6. Prompt Files with Metadata Headers

Some teams add structured frontmatter to prompt files:

```markdown
---
title: "Add new API endpoint"
model: claude-sonnet-4
temperature: 0.2
context: [SPEC.md, HACKERS.md]
---
```

This makes prompts self-documenting and portable between AI tools.

---

## 7. What This Means for Pendula

| Practice | Status | Next step |
|----------|--------|-----------|
| `HACKERS.md` | ✅ Done | Already in place |
| `AGENTS.md` alias | 🔄 Could symlink or duplicate | Low priority |
| `.specs/` folder | ❌ Not yet | Consider adding if project grows |
| Prompt library | ❌ Not yet | Deferred |
| SPDD workflow | ❌ Not yet | Deferred |

The biggest gap: we have no `SPEC.md` or product brief. The `prompt.txt` files in the repo are session prompts, not a persistent product spec. If the project matures, a `/.specs/` folder with a `SPEC.md` (architecture, data model, roadmap) would anchor AI agents more effectively than session-only prompts.

---

## Sources

- [Building shared coding guidelines for AI (and people too) — Stack Overflow Blog](https://stackoverflow.blog/2026/03/26/coding-guidelines-for-ai-agents-and-people-too/)
- [Context Engineering Best Practices — Packmind](https://packmind.com/context-engineering-ai-coding/context-engineering-best-practices/)
- [How to write a good spec for AI agents — Addy Osmani](https://addyosmani.com/blog/good-spec/)
- [Structured-Prompt-Driven Development — Martin Fowler / Thoughtworks](https://martinfowler.com/articles/structured-prompt-driven/)
- [Building AI-First Codebases — The Rice Stack](https://thericestack.substack.com/p/building-ai-first-codebases)
- [Spec-driven development with AI — GitHub](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/)
