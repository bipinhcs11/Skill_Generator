# Skill Generator v2 — Progress Report

Date: 2026-05-18
Branch: feat/v2-foundation
Session: Milestone 0 + Milestone 1 foundation pass

---

## Current status addendum

After the follow-up docs and flow refinement, the branch now includes:

- `skills/skill-tracker/SKILL.md` as the read-only PR/change impact detector.
- Updated README agent-role guidance: generator, tracker, updater, validator.
- Updated invocation flow diagrams showing tracker before updater.
- Updated enterprise rollout guidance and release checklist for the tracker/updater split.
- Added `docs/templates/copilot-instructions.md` for target repos that use GitHub Copilot.
- GitHub repo established at `https://github.com/bipinhcs11/Skill_Generator`; `main` and `feat/v2-foundation` currently carry the v2 foundation commits.

Historical workspace notes below describe how the v2 repo was originally carved
out. They are kept for traceability, not as current onboarding instructions.

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

- `lib/validate.py` — structural enforcement (172 LOC)
  - Frontmatter field presence and type checking
  - Confidence/review-required metadata checks
  - Optional dependency-list shape checks
  - Section-order validation
  - PLACEHOLDER, "none found", java fence detection

- `lib/citation_check.py` — citation presence (81 LOC)
  - Checks `## Key Classes and Responsibilities` and `## Data Flow`
  - Does NOT check that cited classes exist (that is skill-validator's job)

- `lib/frontmatter.py` — parse/serialize (94 LOC)
  - Handles edge cases without PyYAML (stdlib-only)
  - `bump_version()` for skill-updater use

- `lib/audit_log.py` — evidence artifact formatter (147 LOC)
  - Stable, diff-friendly Markdown output
  - All data structures for evidence blocks, validation results, review queues,
    and cross-feature dependencies

- **Total lib/ LOC: 494** (target ~300, hard cap 500 — within spec, little headroom)

- `skills/skill-validator/SKILL.md` — artifact-3 contract enforcement
  - 6-step deterministic/semantic checklist
  - Self-correction rules (two allowed types, two-attempt limit)
  - Verdict format (PASS, PASS_WITH_SELF_CORRECTIONS, NEEDS_REVIEW, BLOCKING_ISSUES)
  - Multi-file validation summary format
  - When-to-run table

- `skills/skill-updater/SKILL.md` — Phase 2 update contract
  - Maps Java/properties/MyBatis XML/SQL/Spring Batch/script diffs to affected feature skills
  - Propagates updates through `depends_on` / `depended_on_by`
  - Maintains dependency metadata and Integration Points on both sides
  - Writes `.github/skills/.skill-update-audit.md`

- `README.md` — v2 root documentation
- `CLAUDE.md` — Claude Code project rules for this repo
- `.gitignore`

**Not yet started (later milestones):**

- Production-hardening `skills/skill-updater/SKILL.md` with real-repo tests
- `AGENT.md` / `AGENTS.md` (Milestone 6)
- Petclinic re-test (Milestone 3 — requires running the full skill-generator
  skill against petclinic and comparing to v1 output at `~/Documents/petclinic-skill-test/`)
- `docs/agent-invocation-flow.md` update (still shows v1 pipeline; needs evidence
  phase added to the Mermaid diagram)
- `docs/release-readiness-checklist.md` rewrite for v2

---

## Architectural decisions made this session

### Decision 1: lib/ is 494 LOC, not ~300

Target was ~300, hard cap 500. We landed at 494. The extra LOC is in:
- `audit_log.py` (147 LOC): the data classes and table formatters are genuinely
  needed for stable evidence, review-queue, and dependency diffs. Could be
  trimmed by using plain dicts, but the type safety is worth the LOC.
- `frontmatter.py` (94 LOC): the edge-case handling (nested lists, bare keys,
  quoted values) is why this exists as a separate file.

**Verdict:** 494 LOC is still inside the hard cap, but leaves almost no headroom.
For now `audit_log.py` counts inside the 500 LOC budget. If the next enterprise
repo test needs more deterministic support, raise the cap through a
design-history decision rather than quietly growing `lib/`.

### Decision 2: LOW confidence generates a review-required draft

LOW confidence is now a developer review signal, not an automatic generation
block. Generated skills carry `confidence` and `review_required`; LOW confidence
must set `review_required: true`. This matches the enterprise goal: generate as
much useful feature context as possible, while giving leads a clear review queue.

### Decision 3: Dependencies are first-class metadata

Feature dependencies now live in `depends_on` and `depended_on_by`, with prose in
`## Integration Points`. The updater uses this graph to propagate changes across
feature boundaries, such as participant changes that affect invoice comparison.

### Decision 4: skill-validator is agent-only (no new lib file)

The validator is a SKILL.md, not a Python file. Considered adding a
`lib/contract_check.py` to automate the package/class existence checks, but
this crosses the architectural boundary: it would be a crawler in lib/. The
agent runs `find` and `grep` with its own tools. The lib boundary holds.

### Decision 5: self-correction limited to two types, two attempts

The original proposal said "agent self-corrects on failure." Without explicit
limits, self-correction loops can obscure underlying problems. Two types, two
attempts per file is the explicit operating contract. Surfacing to the developer
after two attempts is the right default.

### Decision 6: docs/agent-invocation-flow.md not updated yet

The v1 diagram does not show the evidence phase. Updating it requires Mermaid
editing and is a half-day task worth its own commit. Deferred to the next
session to keep this session's scope clean.

---

## Open risks

| Risk | Severity | Mitigation |
|---|---|---|
| Silent plausible wrongness on the first real-repo run | High | Evidence phase + halt gates designed for this; petclinic re-test is the first gate |
| lib/frontmatter.py edge cases not covered | Medium | The most critical edge cases are handled; real-repo test will surface others |
| skill-updater is the hardest milestone | High | Initial contract exists; still needs real-repo diff testing for change-impact analysis, stale-skill detection, and dependency propagation. |
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

2. **Create or migrate one artifact-3 fixture skill and run `lib/validate.py` +
   `lib/citation_check.py` against it.** The three preserved reference skills are
   v1 schema examples; migrate them before using them as v2 validator fixtures.

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
skills/skill-updater/SKILL.md
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
feat: lib — deterministic structural spine (494 LOC, within 500 cap)

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

Add SKILL.md covering: 6-step deterministic checklist, self-correction
rules (2 types, 2 attempts), verdict format, multi-file summary.
```

```
feat: skills/skill-updater — dependency-aware update workflow

Add SKILL.md covering: diff intake, impact analysis, dependency propagation,
review gates, validation, and update audit logging.
```

```
docs: add README, CLAUDE.md, v2-progress-report
```

---

## What is explicitly not done

- No CI integration
- No production hardening
- No production-hardened skill-updater real-repo test yet
- No petclinic re-test (next session priority)
- No GitHub repo or push
- No merge to main
