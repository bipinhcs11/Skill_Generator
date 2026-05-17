# Claude Code project rules — Skill Generator v2

## Workflow rules (non-negotiable)

- Never commit directly to `main`.
- Always work on a feature branch named `feat/v2-<scope>`.
- Make small, logical commits. One concern per commit.
- Stop before merge. The developer reviews and merges manually.
- Preserve `legacy/FeatureBased_Skill_Generator_Agent/` completely.
  Do not delete, rename, or modify any file under `legacy/`.

## Lib boundary rule

The `lib/` directory is the deterministic structural spine. Hard cap: 500 LOC combined.
Adding any semantic analysis to `lib/` (domain inference, crawler logic, planner
heuristics) requires an explicit decision record in `docs/design-history/`.
If you are not sure whether something belongs in `lib/`, the answer is no.

What belongs in `lib/`: frontmatter parsing, section-order validation,
citation regex checks, audit-log formatting.

## Commit message format

Use the conventional commits prefix appropriate to the change:
- `feat:` for new capability
- `fix:` for bug correction
- `docs:` for documentation only
- `test:` for test additions
- `refactor:` for internal restructure with no behavior change

Always include `Co-Authored-By: <developer>` if working alongside the developer.

## Documentation style

- Plain English. Short sentences. Decision tables over prose lists.
- No internal jargon in user-facing documents.
- Write as if the reader is a competent developer who has never seen this repo.
- The bar is Codex / Anthropic-course style documentation.

## Real-repo testing rule

Unit tests and reference regression tests are not enough. Before claiming
any pipeline change is ready, run it on a real Java repo and observe actual
output. The petclinic test is the regression baseline.

## Enterprise architect mindset

When the developer mentions "10 teams", "150 developers", or "premium request
budget" — that is a rollout and ownership question, not a code question.
Answer it as an architect: rollout plan, ownership model, support model.
Do not answer it with code.
