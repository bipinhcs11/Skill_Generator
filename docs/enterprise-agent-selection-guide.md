# Enterprise agent selection guide

This guide is for engineering managers, platform teams, and feature leads who want Skill Generator v2 to help many Java developers without burning the same GitHub Copilot premium requests over and over.

The short version: use stronger reasoning sessions to create and review shared `SKILL.md` files once, then let everyday developers consume those committed skills from Copilot, Claude, or Codex inside VS Code or IntelliJ.

---

## Why agent selection matters

Most teams should not ask every developer to regenerate skills. That duplicates premium usage and creates inconsistent context. Treat skill generation like creating a shared architecture artifact:

1. A repo owner or feature lead runs the generator.
2. The team reviews the generated features and `SKILL.md` files.
3. The skills are committed under `.github/skills/<feature-id>/SKILL.md`.
4. Developers use their normal IDE assistant with the committed skills as durable feature context.
5. Updates are run only when feature behavior changes.

This turns a small number of up-front host-agent turns into reusable context for everyone on the repo.

---

## Recommended model/session matrix

| Workload | Recommended host session | Why |
|---|---|---|
| First run on an unknown repo | Claude Opus-class session or Codex with high reasoning | Highest need for feature-boundary judgment, older-system detection, and careful source synthesis. |
| First run on a clean Spring Boot service | Claude Sonnet-class session or Codex | Usually enough for package/controller/service/DAO grouping when the codebase is well structured. |
| Older complex module with Struts, XML, stored procedures, or shell orchestration | Strongest available reasoning session | More ambiguity, more cross-file inference, and higher risk of wrong business boundaries. |
| Plan review and feature rename/merge decisions | Feature lead + any capable host session | The human feature owner is the authority; the model helps summarize tradeoffs. |
| PR impact tracking | Claude Sonnet-class session, Codex, or Copilot Chat | The tracker is read-only and decides whether any skill update is needed before rewrite work starts. |
| Incremental skill update for one touched feature | Claude Sonnet-class session, Codex, or Copilot Chat | The source slice is smaller and the existing skill constrains the rewrite. |
| Everyday feature questions and code changes | GitHub Copilot Chat in VS Code/IntelliJ, Claude, or Codex reading `.github/skills` | The committed skill is the durable context, so daily work should not require re-discovery. |
| Cross-feature change review | Stronger reasoning session if multiple skills are affected | Cross-feature contract changes are where regressions hide. |

Use “Opus-class” and “Sonnet-class” as capability tiers rather than hard product requirements. The tool itself has no model setting; the selected host AI session supplies the reasoning.

---

## IDE usage pattern

| IDE / surface | Best use | Notes |
|---|---|---|
| VS Code + GitHub Copilot Chat | Day-to-day feature questions, code edits, and skill consumption | Use `docs/templates/copilot-instructions.md` as the target repo `.github/copilot-instructions.md` so Copilot knows to read `.github/skills` first. |
| VS Code + Codex | Running the generator workflow, reviewing evidence artifacts, deeper repo analysis | Good fit when the developer wants an agent to inspect files and drive the v2 skill workflow. |
| IntelliJ + Copilot Chat | Day-to-day Java work once skills are committed | Works best when skills are already in the repo and indexed with the workspace. |
| IntelliJ + external Claude/Codex session | First-run generation or older-system analysis while coding remains in IntelliJ | The prompt files are plain markdown, so the host session does not need to be the same UI used for Java editing. |
| Claude Code / Claude desktop-style sessions | First-run generation, ambiguous older systems, and high-quality SKILL.md drafting | Strong for source synthesis and long-form structured output. |

The implementation intentionally keeps semantic analysis inside the approved host AI session and structural enforcement inside the small `lib/` spine. That means an enterprise can allow multiple IDEs and multiple approved model providers without changing the generated skill contract.

---

## Operating model for 10 teams

For an organization with many Java repos, use a shared ownership model:

| Role | Responsibility |
|---|---|
| Platform / architecture team | Owns this generator, templates, release readiness, and enterprise instructions. |
| Repo owner | Runs first generation or delegates it, commits `.github/skills`, and decides which features are in scope. |
| Feature lead | Reviews generated skill content for business correctness before the first commit. |
| Developers | Consume skills during normal Copilot/Claude/Codex work and request updates when behavior changes. |
| PR reviewer | Runs or requests `skills/skill-tracker/SKILL.md`; approves `skills/skill-updater/SKILL.md` only for impacted skills. |

Do not make every developer choose the model from scratch. Publish a team default, then allow escalation to a stronger model for difficult repos.

---

## Recommended rollout

Start with a controlled pilot:

1. Pick 2-3 representative Java repos: one clean Spring Boot service, one older XML/Struts-style module if available, and one batch or scheduled job repo.
2. Run `skills/skill-generator/SKILL.md`; review the evidence blocks, confidence levels, and proposed dependencies.
3. Approve the plan or ask the agent to merge, split, rename, or exclude features.
4. Validate with `$SKILL_GENERATOR_HOME/lib/validate.py` and `$SKILL_GENERATOR_HOME/lib/citation_check.py`.
5. Copy `docs/templates/copilot-instructions.md` into the target repo as `.github/copilot-instructions.md`.
6. Ask developers to use Copilot/Claude/Codex against those committed skills for one sprint.
7. Measure whether common feature questions now resolve in one turn instead of repeated context setup.
8. Use `skills/skill-tracker/SKILL.md` for one real PR and verify the impact report is accurate.
9. Use `skills/skill-updater/SKILL.md` only for the approved impacted skills and verify only affected skills changed.
10. Expand to the rest of the repo only after feature leads trust the first skills.

For enterprise rollout, the platform team should maintain a short internal runbook that records which host session tier is approved for first-run generation and which tier is preferred for routine updates.

---

## Premium-request budget guidance

The generator is designed around the reality that many enterprise developers have a small monthly premium-request allowance. The goal is not to eliminate premium requests; it is to stop spending them on the same feature rediscovery.

For a typical 10-feature repo:

| Activity | Approximate host-agent turns | Who should spend them |
|---|---:|---|
| Initial plan | 1 | Repo owner / feature lead |
| Generate 10 feature skills | 10 | Repo owner / feature lead |
| Link skills | 1 | Repo owner / feature lead |
| Everyday feature questions after commit | Usually 1 per question | Any developer, with skills loaded |
| PR impact tracking | Usually 1 | PR reviewer or PR author |
| Incremental update after a PR | Usually 1 per affected feature | Feature owner or PR author |

The return on investment comes when those 12-ish initial turns replace dozens or hundreds of repeated “here is how this feature works” prompts across the team.

---

## Decision rules

Use the strongest available model/session when:

- The repo is older, XML-heavy, stored-procedure-driven, or has unclear package boundaries.
- A feature spans multiple modules or asynchronous workflows.
- The first generated plan has low confidence or surprising feature splits.
- The skill will be used by many developers or many downstream repos.

Use the default team model/session when:

- The repo is clean Spring Boot / Quarkus with obvious package boundaries.
- You are refreshing one already-reviewed skill after a small PR.
- The update only changes a DTO, validation rule, endpoint path, or enum value.

Use Copilot/Claude/Codex day to day after skills are committed:

- Ask “read `.github/skills/<feature>/SKILL.md` first” when the assistant does not automatically load the right skill.
- Treat the skill as authoritative over training knowledge.
- Run the tracker when a PR may change captured behavior, then trigger an update only for impacted skills.

---

## What this does not solve yet

This guide improves adoption, not core pipeline accuracy. The release-readiness checklist still governs whether the generator is ready for unsupervised enterprise-wide rollout. In particular, chunk-and-merge for very large features, stronger end-to-end verification, and multi-repo orchestration remain separate delivery items.
