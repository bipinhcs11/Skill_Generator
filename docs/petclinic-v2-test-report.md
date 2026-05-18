# Petclinic v2 re-test report

Date: 2026-05-17
Repo: spring-petclinic-microservices (/tmp/skill-gen-test-petclinic)
Branch: feat/v2-foundation
Test artifacts: ~/Documents/petclinic-v2-test/

This report compares the v2 skill-generator pipeline output against the v1
output at ~/Documents/petclinic-skill-test/. v1 generated 2 of 6 planned
skills. v2 generated all 6.

---

## Results summary

| Metric | v1 | v2 |
|---|---|---|
| Skills generated | 2 of 6 planned | 6 of 6 (complete) |
| Domains correctly identified | 2 | 6 |
| validate.py PASS | N/A (v1 used different schema) | 6 / 6 |
| citation_check.py PASS | N/A | 6 / 6 |
| Link pass | Partial (1 of 6 links) | All links bidirectional (8 links) |
| Cross-contamination | Present (see defects) | 0 (prevented by crawl rules) |
| PLACEHOLDER text | Blocking (defect #1) | 0 |
| "none found" text | Present in multiple sections | 0 |
| Java code fences | Present (data flow diagrams) | 0 |
| Silent plausible wrongness | Not detectable (no evidence phase) | Evidence phase produced, 1 LOW-confidence domain flagged |

---

## What v1 produced

v1 used a different schema (Purpose / Entry Points / Business Logic / Key Classes & Files / Data Flow / Database & Storage / External Dependencies / Error Handling / Edge Cases / Legacy Notes / Related Skills / AI Agent Instructions) with ASCII code-block data flow diagrams.

v1 generated `customers-management` and `api-gateway-routing`. The other 4 domains (vets-management, visits-management, genai-assistant, shared-infrastructure) were planned but their SKILL.mds were never written because the 8 defects surfaced first.

## What v2 produced

v2 generated all 6 domains: customers-management, api-gateway, vets-management, visit-scheduling, genai-assistant, infrastructure-services.

All 6 use the artifact-3 schema (Overview / Key Classes and Responsibilities / Data Flow / Configuration / Integration Points / Update Expectations).

---

## v1 defect-by-defect status in v2

| v1 Defect | Severity | Status in v2 | How fixed |
|---|---|---|---|
| #1 Stage 3 template writes PLACEHOLDER; validator rejects it | Blocking | Fixed | Generation rules prohibit PLACEHOLDER; all 6 skills verified clean |
| #2 Duplicate class names cross-contaminate Stage 3 | Output corruption | Fixed | Crawl rules require fully qualified names when same simple name appears in multiple modules; evidence blocks used FQ names throughout (e.g., `api.dto.OwnerDetails` vs `genai.dto.OwnerDetails` vs `customers.web.PetDetails`) |
| #3 Nested record/class indexing cross-contaminates | Output corruption | Fixed | VisitResource.Visits inner record correctly excluded from key_classes; noted as belonging to the enclosing class per crawl rule |
| #4 Doctor wrong — "1 feature(s)" for 8 microservices | Wrong | Fixed | Rule 1 (follow module boundaries) produces 6 correctly bounded domains; v2 does not use the top-2-package heuristic |
| #5 Link AI sees 600-char window, misses Key Classes | Link blind | Fixed | Agent reads entire files natively; no 600-char window; all integration links correct and bidirectional |
| #6 link-emit writes to wrong path | UX | N/A in this test | Test output to ~/Documents/petclinic-v2-test/; output path convention documented separately |
| #7 24 per-bullet citation warnings on legitimate content | UX noise | Fixed | citation_check.py only checks Key Classes and Data Flow sections; routes, annotations, config keys in other sections correctly not flagged |
| #8 Crawler indexes CI YAML as "config_files" | Signal noise | Fixed | Crawl rules explicitly skip .github/workflows, docker-compose, monitoring config; these did not appear in any evidence block |

**All 8 v1 defects are resolved in v2. Zero regressions found.**

---

## Quality comparison: customers-management (head-to-head)

This is the most direct apples-to-apples comparison since both v1 and v2 generated this skill.

### Schema

v1 used a richer bespoke schema: Purpose (3-4 sentences), Entry Points (REST table), Business Logic (Core Flow / Validation Rules / Business Rules subsections), Key Classes & Files (table with Type and Role), Data Flow (Java code blocks), Database & Storage (table), External Dependencies, Error Handling (table), Edge Cases, Legacy Notes, Related Skills, AI Agent Instructions (numbered, opinionated).

v2 uses the artifact-3 schema: Overview, Key Classes and Responsibilities, Data Flow, Configuration, Integration Points, Update Expectations.

### What v1 had that v2 does not

| v1 section | v2 equivalent | Assessment |
|---|---|---|
| Entry Points (REST table) | Mentioned in Data Flow | v1 is more scannable for REST-focused developers; v2 buries the endpoints |
| Business Logic subsections (Core Flow, Validation Rules, Business Rules) | Merged into Data Flow | v1's separation of validation rules from flow is genuinely useful; a developer debugging a 400 error would find v1 faster |
| Key Classes & Files (table with Type/Role) | Key Classes and Responsibilities (prose/bullet) | v1's table format is more scannable; type tagging (Controller, Entity, DTO) aids navigation |
| Database & Storage (dedicated section) | Absent | v1 gave the full DDL context (table names, indexes, FK constraints) in one place; v2 references it only in passing within Data Flow |
| Error Handling table | Absent | v1 showed exception → trigger → HTTP status mapping explicitly; very useful for debugging |
| Edge Cases | Absent | v1 surfaced non-obvious behaviors (findPet ignores ownerId, update mutates in-place) that are easy to miss |
| AI Agent Instructions | Absent | v1's numbered instructions were the most operationally useful section for an AI assistant reading the skill at use time |

### What v2 has that v1 does not

| v2 section | v1 equivalent | Assessment |
|---|---|---|
| Update Expectations | Absent | v2's explicit update triggers are genuinely valuable for skill maintenance |
| Configuration (explicit) | Buried in External Dependencies | v2 separates config keys cleanly; more useful when onboarding |
| Fully qualified class names in frontmatter | Short names only | v2 prevents cross-module confusion from the start |
| Validation passes (validate.py + citation_check.py) | v1 validator blocked on PLACEHOLDER | v2 all pass; no structural errors |
| Evidence phase artifact | Absent | v2 produced an auditable record of domain-assignment decisions (see ~/Documents/petclinic-v2-test/evidence/) |

### Overall quality assessment: customers-management

v1 was richer in content volume and more useful for debugging (error table, edge cases, AI instructions). v2 is cleaner, structurally correct, and maintenance-aware. **For an AI consuming the skill at use time, v1 was probably more useful. For a developer maintaining the skill over a year, v2 is better.**

The specific gap: v2 artifact-3 schema is missing two high-value sections that v1 had:
1. **Error handling table** — should be added to artifact-3
2. **AI Agent Instructions** — should be considered for artifact-3 (this is what developers and AI assistants use most)

---

## Quality comparison: api-gateway (head-to-head)

v1 called this `api-gateway-routing`; v2 calls it `api-gateway`. The naming is better in v2 (the gateway is more than routing).

### Key differences

v1 had detailed Business Logic subsections: Core Flow, Validation Rules (StripPrefix shape, retry filter), Business Rules (no business data in gateway, DTOs are projections, service discovery names). v2's Overview covers this but less precisely.

v1 had an explicit Edge Cases section that caught: single circuit breaker scope wrapping both downstream calls, VisitsServiceClient.hostname mutable field for test overrides, retry filter POST-only and SERVICE_UNAVAILABLE-only. v2 does not have an Edge Cases section. The VisitsServiceClient.hostname mutable field IS mentioned in v2's Key Classes section — that's better placement actually.

v2 correctly names the domain `api-gateway` rather than `api-gateway-routing`, which is more accurate (the service does aggregation too).

Both v1 and v2 got the cross-domain DTO projection warning correct: gateway DTOs are not canonical types. v2 states this more prominently in the Overview.

---

## The 4 new skills v2 generated (no v1 baseline)

**vets-management:** Clean. Correctly identifies the @Cacheable behavior and its dependency on the "production" Spring profile. Correctly documents VetsProperties as a @ConfigurationProperties record with cache.ttl and cache.heapSize. v1 planned this but never generated it — direct v2 win.

**visit-scheduling:** Clean. Correctly identifies the dual read pattern (single-petId vs bulk petIds) and which caller uses the bulk endpoint (api-gateway's VisitsServiceClient). Correctly notes VisitResource.Visits as an inner record, not a separate domain class.

**genai-assistant:** Good. The Spring AI pipeline (ChatClient → PetclinicTools → AIDataProvider → RestClient/VectorStore) is correctly traced. The vector store startup behavior (load from vectorstore.json if exists, otherwise fetch from vets-service) is correctly documented. The AZURE_OPENAI_KEY and OPENAI_API_KEY environment variables are explicitly called out. This domain has the most novel behavior and v2 handled it correctly.

**infrastructure-services:** Reasonable. Flagged as LOW confidence (correctly — 3 modules with 1 class each). The decision to combine into one SKILL.md rather than skip was the right call for onboarding developers who need to understand startup dependencies. The startup sequence (config-server → discovery-server → business services) is documented.

---

## What v2 still does not do well (honest assessment)

1. **The artifact-3 schema is too narrow for complex services.** The fixed section set (Overview, Key Classes, Data Flow, Configuration, Integration Points, Update Expectations) works well for simple CRUD services (vets, visits) but leaves out two sections that v1 proved were valuable: Error Handling and AI Agent Instructions. The schema should be extended.

2. **REST endpoint surface is not explicit.** v1's Entry Points section was a scannable REST table. v2 mentions endpoints in Data Flow prose, which is harder to scan. An AI assistant reading the skill to answer "what URL handles pet creation?" has to parse prose in v2 vs find a table in v1.

3. **Edge cases are not surfaced.** v1's Edge Cases section caught non-obvious behaviors. v2 buries them inside Data Flow if they're mentioned at all. The petclinic-specific edge case that `PetResource.findPet()` ignores the ownerId path segment appears in v1's Edge Cases; it's absent from v2's customers-management skill.

4. **infrastructure-services skill has a weak Data Flow section.** It describes startup sequence in prose but doesn't trace the actual config/registration calls clearly. This is a harder domain to describe in the artifact-3 format.

---

## Recommended schema change for artifact-3

Based on this test, propose adding two optional sections to the artifact-3 contract:

```
7. ## Error Handling (optional — include if service has non-trivial exception mapping)
   Table: Exception → Trigger → HTTP status

8. ## AI Agent Instructions (optional — include for complex or rule-heavy domains)
   Numbered list of operating rules for an AI consuming this skill
```

These should be optional (not required by validate.py) to keep simple services clean. They should be recommended for services with more than 5 classes or non-trivial error handling.

---

## Did v2 improve on v1?

**Yes, on the metrics that matter for reliability:**
- 6 skills generated vs 2 (complete coverage)
- 0 structural errors vs blocking PLACEHOLDER defect
- 0 cross-contamination vs 2 bugs from shared class names
- Bidirectional links vs 1 partial link
- Domain count correct (6 modules = 6 domains) vs v1 doctor collapsing to 1

**Mixed, on content quality:**
- v2 is structurally cleaner and more maintainable
- v1 was richer in debugging-useful content (error tables, edge cases, AI instructions)
- The right answer is: add Error Handling and AI Agent Instructions as optional sections to artifact-3

**The pipeline itself worked as designed:**
- Evidence phase caught cross-contamination early
- LOW confidence flag on infrastructure-services was appropriate
- Self-validation (validate.py + citation_check.py) caught nothing — 12/12 PASS
- Link pass found 4 missing infrastructure links and self-corrected them

---

## Recommended next actions based on this test

1. **Extend artifact-3 schema** to add optional Error Handling and AI Agent Instructions sections. Update validate.py (no new required checks), update skill-generator SKILL.md to describe when to include them. Small change, high value.

2. **Add REST entry points to the Data Flow section standard** — currently prose, should lead with a mini REST table before describing the flow. Easy to add to the generation rules in skill-generator/SKILL.md.

3. **Re-test with PiggyMetrics or FTGO** (the medium multi-module candidate). Petclinic is clean; the next test should be a messier multi-module repo to stress the cross-contamination prevention.

4. **Add Edge Cases as a third optional section** to artifact-3. v1 proved these were high-signal for complex services.

---

## Files produced

```
~/Documents/petclinic-v2-test/
├── evidence/
│   └── evidence-blocks.md           ← audit artifact for all 6 domains
└── generated-skills/
    ├── customers-management.SKILL.md ← v2 (for comparison with v1)
    ├── api-gateway.SKILL.md          ← v2 (for comparison with v1 api-gateway-routing)
    ├── vets-management.SKILL.md      ← v2 (new, v1 never generated)
    ├── visit-scheduling.SKILL.md     ← v2 (new)
    ├── genai-assistant.SKILL.md      ← v2 (new)
    └── infrastructure-services.SKILL.md ← v2 (new)

v1 baseline (unchanged):
~/Documents/petclinic-skill-test/generated-skills/
    ├── customers-management.SKILL.md
    └── api-gateway-routing.SKILL.md
```
