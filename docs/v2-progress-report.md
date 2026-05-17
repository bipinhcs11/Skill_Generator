# Skill Generator v2 — Progress Report

Date: 2026-05-17
Branch: feat/v2-foundation
Session: Milestone 0 + Milestone 1 foundation pass

---

## What was completed this session

### Milestone 0 — Workspace reorganization (complete)

- Created `Customized_Agent_For_Developers/legacy/`
- Moved `FeatureBased_Skill_Generator_Agent/` into `legacy/` — fully preserved,
  including the untracked `AGENTS.md` from Codex's earlier session
- Created `Customized_Agent_For_Developers/Skill_Generator/` as the v2 root
- Initialized a new git repo in `Skill_Generator/`
- Created the feature branch `feat/v2-foundation`
- Copied the keep-list from v1:
  - Reference skills: `file-delivery`, `invoice-compare`, `payment-method-determination`
  - Preserved docs: `enterprise-agent-selection-guide.md`, `agent-invocation-flow.md`,
    `release-readiness-checklist.md`, `design-history/`
  - Preserved: `LICENSE`, `OPUS_PROMPT.md`
  - Preserved examples: all three reference example sets

**What was not copied (intentionally dropped):**
- `tools/skill_generator/` — the semantic-analysis Python pipeline (crawler, planner,
  generator, linker, doctor). This is the pivot. It lives in `legacy/` only.
- `tests/` — most tests targeted the Python pipeline and will not survive the pivot.
  v2 tests will be written after milestone 3 (petclinic re-test defines what to test).
- `verification-output/` — v1 test artifacts. Not relevant to v2.

### Milestone 1 — Foundation content (in progress)

**Completed:**

- `skills/skill-generator/SKILL.md` — the full agent contract
  - Pre-flight, crawl rules, evidence-phase template with confidence levels,
    Halt Gate 1, generation rules, artifact-3 contract, self-validation,
    link pass, Halt Gate 2, commit, audit log format
  - Crawl rules for grouping (5 rules in priority order)
  - Good and bad grouping examples (petclinic collapse bug documented)
  - Cross-contamination prevention rules
  - Silent plausible wrongness explicitly defended against

- `lib/validate.py` — structural enforcement (151 LOC)
  - Frontmatter field presence and type checking
  - Section-order validation
  - PLACEHOLDER, "none found", java fence detection

- `lib/citation_check.py` — citation presence (76 LOC)
  - Checks `## Key Classes and Responsibilities` and `## Data Flow`
  - Does NOT check that cited classes exist (that is skill-validator's job)

- `lib/frontmatter.py` — parse/serialize (92 LOC)
  - Handles edge cases without PyYAML (stdlib-only)
  - `bump_version()` for skill-updater use

- `lib/audit_log.py` — evidence artifact formatter (110 LOC)
  - Stable, diff-friendly Markdown output
  - All data structures for evidence blocks, validation results, cross-domain links

- **Total lib/ LOC: 429** (target ~300, hard cap 500 — within spec)

- `skills/skill-validator/SKILL.md` — artifact-3 contract enforcement
  - 5-step deterministic checklist
  - Self-correction rules (two allowed types, two-attempt limit)
  - Verdict format (PASS, PASS_WITH_SELF_CORRECTIONS, NEEDS_REVIEW, BLOCKING_ISSUES)
  - Multi-file validation summary format
  - When-to-run table

- `README.md` — v2 root documentation
- `CLAUDE.md` — Claude Code project rules for this repo
- `.gitignore`

**Not yet started (later milestones):**

- `skills/skill-updater/SKILL.md` (Milestone 5 in proposal — 2-3 days)
- `AGENT.md` / `AGENTS.md` (Milestone 6)
- Petclinic re-test (Milestone 3 — requires running the full skill-generator
  skill against petclinic and comparing to v1 output at `~/Documents/petclinic-skill-test/`)
- `docs/agent-invocation-flow.md` update (still shows v1 pipeline; needs evidence
  phase added to the Mermaid diagram)
- `docs/release-readiness-checklist.md` rewrite for v2

---

## Architectural decisions made this session

### Decision 1: lib/ is 429 LOC, not ~300

Target was ~300, hard cap 500. We landed at 429. The extra LOC is in:
- `audit_log.py` (110 LOC): the data classes and table formatters are genuinely
  needed for stable diffs. Could be trimmed by removing the `CrossDomainLink`
  and `ValidationResult` dataclasses and using plain dicts — but the type safety
  is worth 20 LOC.
- `frontmatter.py` (92 LOC): the edge-case handling (nested lists, bare keys,
  quoted values) is why this exists as a separate file.

**Verdict:** 429 LOC is fine. The hard cap is 500 for a reason; 429 gives
headroom for the next real-repo test to surface edge cases.

### Decision 2: skill-validator is agent-only (no new lib file)

The validator is a SKILL.md, not a Python file. Considered adding a
`lib/contract_check.py` to automate the package/class existence checks, but
this crosses the architectural boundary: it would be a crawler in lib/. The
agent runs `find` and `grep` with its own tools. The lib boundary holds.

### Decision 3: self-correction limited to two types, two attempts

The original proposal said "agent self-corrects on failure." Without explicit
limits, self-correction loops can obscure underlying problems. Two types, two
attempts per file is the explicit operating contract. Surfacing to the developer
after two attempts is the right default.

### Decision 4: docs/agent-invocation-flow.md not updated yet

The v1 diagram does not show the evidence phase. Updating it requires Mermaid
editing and is a half-day task worth its own commit. Deferred to the next
session to keep this session's scope clean.

---

## Open risks

| Risk | Severity | Mitigation |
|---|---|---|
| Silent plausible wrongness on the first real-repo run | High | Evidence phase + halt gates designed for this; petclinic re-test is the first gate |
| lib/frontmatter.py edge cases not covered | Medium | The most critical edge cases are handled; real-repo test will surface others |
| skill-updater is the hardest milestone | High | Not started; change-impact analysis, stale-skill detection, and semantic-diff interpretation are genuinely harder than first-gen. Budgeted 2-3 days. |
| Context-window scaling on large repos | Medium | v2 targets ≤300 classes; acknowledged as milestone-8 question |
| docs/agent-invocation-flow.md is stale | Low | V1 diagram; needs evidence phase added; deferred to next session |
| No test suite yet | Medium | Python unit tests for lib/ should be written after milestone 3 so the petclinic test defines what to cover |

---

## Unresolved questions

1. **GitHub repo decision:** The proposal deferred this to milestone 1-2.
   Options: (a) new repo for `Skill_Generator/`, (b) push to a new branch on
   `bipinhcs11/Customized_Agent_For_Developer`, (c) wait. Recommend asking the
   developer before the next session. Default remains (c) per the handoff.

2. **Medium and ugly test repos:** The proposal says petclinic → medium
   multi-module → ugly enterprise. The user has not named the medium or ugly
   candidates. PiggyMetrics or FTGO are candidates for medium. Ugly enterprise
   requires access to a real customer repo.

3. **`docs/release-readiness-checklist.md` rewrite:** The v1 checklist references
   the Python pipeline. It needs a v2 rewrite before milestone 6. Low priority
   now; high priority before any team pilot.

4. **AGENTS.md for Codex:** The v1 `AGENTS.md` is in `legacy/`. V2 needs a new
   one scoped to the v2 structure. Deferred to milestone 6 alongside `AGENT.md`.

---

## Recommended next actions

In priority order for the next session:

1. **Commit the current foundation** on `feat/v2-foundation`.
   Suggested commit sequence (below).

2. **Run `lib/validate.py` and `lib/citation_check.py` on the three reference skills**
   (file-delivery, invoice-compare, payment-method-determination) to verify the
   checks are calibrated correctly. These are known-good skills from v1 and
   should pass.

3. **Update `docs/agent-invocation-flow.md`** to add the evidence phase to the
   Mermaid diagram. One focused commit.

4. **Ask the developer for the GitHub repo decision** before any push.

5. **Start the petclinic re-test** (Milestone 3 in the proposal). Clone a fresh
   copy. Do NOT use `/tmp/skill-gen-test-petclinic/` from the v1 test.
   Run `skills/skill-generator/SKILL.md` from a fresh host-agent session.
   Compare output to `~/Documents/petclinic-skill-test/` from the v1 run.

---

## Exact files changed this session

**New files (Skill_Generator/):**
```
.gitignore
README.md
CLAUDE.md
docs/v2-progress-report.md       ← this file
lib/validate.py
lib/citation_check.py
lib/frontmatter.py
lib/audit_log.py
skills/skill-generator/SKILL.md
skills/skill-validator/SKILL.md
```

**Copied from legacy/FeatureBased_Skill_Generator_Agent/ (unchanged):**
```
skills/file-delivery/SKILL.md
skills/invoice-compare/SKILL.md
skills/payment-method-determination/SKILL.md
examples/file-delivery/
examples/invoice-compare/
examples/payment-method-determination/
docs/enterprise-agent-selection-guide.md
docs/agent-invocation-flow.md
docs/release-readiness-checklist.md
docs/design-history/
LICENSE
OPUS_PROMPT.md
```

**Workspace changes (not inside Skill_Generator/ git repo):**
```
Customized_Agent_For_Developers/legacy/FeatureBased_Skill_Generator_Agent/  ← moved here from root
Customized_Agent_For_Developers/Skill_Generator/                            ← new
```

---

## Branch and suggested commit sequence

**Branch:** `feat/v2-foundation`

**Suggested commit sequence (not yet committed):**

```
feat: milestone 0 — workspace reorganization and v2 folder structure

Move v1 to legacy/; create Skill_Generator/ with full directory structure;
copy keep-list (reference skills, docs, examples, LICENSE, OPUS_PROMPT.md);
initialize git repo on feat/v2-foundation branch.
```

```
feat: lib — deterministic structural spine (429 LOC, within 500 cap)

Add validate.py, citation_check.py, frontmatter.py, audit_log.py.
Architectural boundary: structural enforcement only; no semantic analysis.
```

```
feat: skills/skill-generator — full agent contract with evidence phase

Add SKILL.md covering: pre-flight, crawl rules, evidence-phase template,
halt gates, generation rules, artifact-3 contract, self-validation,
link pass, audit log, grouping examples, cross-contamination prevention.
```

```
feat: skills/skill-validator — artifact-3 contract enforcement

Add SKILL.md covering: 5-step deterministic checklist, self-correction
rules (2 types, 2 attempts), verdict format, multi-file summary.
```

```
docs: add README, CLAUDE.md, v2-progress-report
```

---

## What is explicitly not done

- No CI integration
- No production hardening
- No skill-updater (deferred)
- No petclinic re-test (next session priority)
- No GitHub repo or push
- No merge to main
