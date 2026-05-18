# Release readiness checklist

Objective gate before Skill Generator v2 is recommended for **unsupervised
enterprise-wide rollout** across many Java repos. It is already useful for a
controlled second-team evaluation where feature leads inspect the generated
evidence and review queue.

Legend: ✅ done · ⏳ in progress / planned · ❌ not started · ⚠️ partial

---

## 1. First-Run Correctness

| | Item | Notes |
|---|---|---|
| ✅ | **Pure-agent generation contract exists** | `skills/skill-generator/SKILL.md` defines pre-flight, crawl, evidence, plan review, generation, validation, dependency pass, audit log, and commit gates. |
| ✅ | **Structural validators are callable from target repos** | `SKILL_GENERATOR_HOME` points to this checkout; validators run from inside the Java repo by absolute path. |
| ✅ | **Frontmatter schema includes confidence and review flags** | `confidence` and `review_required` are required; LOW confidence requires `review_required: true`. |
| ✅ | **Dependency graph is first-class metadata** | `depends_on` and `depended_on_by` are structural fields and must agree with `## Integration Points`. |
| ✅ | **Post-link validation is required** | Any dependency-pass edit must be followed by `validate.py` and `citation_check.py`. |
| ✅ | **Citation checker rejects generic capitalized prose** | Requires `ClassName.methodName()` or fully qualified class name in citation-required sections. |
| ✅ | **MyBatis XML and Spring Batch are explicit evidence sources** | Generator, updater, validator, and audit log all name mapper XML and batch flows directly. |
| ⚠️ | **Petclinic baseline is stale against current schema** | Existing generated Petclinic skills predate `confidence`, `review_required`, and dependency metadata. Regenerate or migrate before using as a regression baseline. |
| ❌ | **Medium/ugly enterprise repo test** | Still needed for MyBatis, Spring Batch, stored procedures, XML-heavy modules, and ambiguous package boundaries. |

---

## 2. Update Correctness

| | Item | Notes |
|---|---|---|
| ✅ | **Tracker contract exists** | `skills/skill-tracker/SKILL.md` defines read-only PR/change impact detection, stale-skill findings, dependency propagation review, and missing-feature detection. |
| ✅ | **Updater contract exists** | `skills/skill-updater/SKILL.md` defines diff intake, direct impact, dependency propagation, new-feature detection, update audit, and commit gates. |
| ✅ | **Tracker/updater split avoids whole-repo churn** | Tracker plans; updater edits only approved affected skills and propagated dependencies. |
| ✅ | **Dependency propagation is defined** | Changes to provider contracts can update dependent skills such as `invoice-compare` depending on `participant`. |
| ✅ | **New feature detection halts for decision** | Updater must ask whether to create a new skill, attach to an existing feature, or leave untracked. |
| ❌ | **Real PR diff tracker test** | Needs a real or fixture PR where tracker flags one direct feature and one dependent propagated skill. |
| ❌ | **Real PR diff updater test** | Needs the updater to apply that tracker plan while touching only approved skills. |
| ❌ | **Removed-dependency test** | Need to verify both sides are removed only when source evidence proves the boundary is gone. |

---

## 3. Output Quality

| | Item | Notes |
|---|---|---|
| ✅ | **Artifact-3 includes operational sections** | Optional Error Handling, Business Rules and Edge Cases, and AI Agent Instructions are part of the generator contract. |
| ✅ | **Review queue is explicit** | LOW-confidence and human-requested review skills surface in final summary and audit log. |
| ⚠️ | **Reference skills still use v1 schema** | `skills/file-delivery`, `skills/invoice-compare`, and `skills/payment-method-determination` remain useful examples but should be migrated before serving as v2 fixtures. |
| ❌ | **Generated and tracked skills verified by a second team** | Required before broader rollout. Measure whether everyday prompts actually need fewer context-setting turns. |

---

## 4. Operability

| | Item | Notes |
|---|---|---|
| ✅ | **Setup path is documented** | README defines `export SKILL_GENERATOR_HOME=/path/to/Skill_Generator`. |
| ✅ | **Model/session guidance exists** | `docs/enterprise-agent-selection-guide.md` recommends stronger sessions for first runs and lighter sessions for updates/daily use. |
| ✅ | **Copilot consumption template exists** | `docs/templates/copilot-instructions.md` tells Copilot to read `.github/skills` and dependency skills before answering or editing. |
| ⚠️ | **`lib/` LOC cap is nearly full** | 494/500 LOC. Future deterministic growth needs consolidation or a design-history decision. |
| ❌ | **Team runbook template** | Each enterprise still needs approved host-session tiers, ownership, and PR review expectations. |
| ❌ | **CI policy for stale skills** | Not implemented. v2 currently assumes human-triggered local agent runs. |

---

## Verdict By Audience

- **Repo authors / hands-on pilot team:** ✅ ready.
- **Second team with feature-lead review:** ✅ ready after Petclinic baseline is regenerated or clearly marked historical.
- **Unsupervised enterprise-wide rollout:** ❌ not yet. Needs medium/ugly repo tests, real PR-diff tracker/updater tests, migrated v2 fixtures, and a team runbook.

This checklist should move only when real repo evidence moves it. The test is the gate.
