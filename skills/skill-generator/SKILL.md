---
skill_id: skill-generator
version: 6
last_updated: "2026-05-18"
trigger_phrases:
  - "analyze this project and generate the feature skills"
  - "generate skill files for this repo"
  - "create feature-based skill files"
  - "run skill generator"
target_language: Java
artifact_contract: artifact-3
---

# Skill Generator v2

## Purpose

This skill turns a Java repository into a complete set of feature-based SKILL.md
files, one per coherent business capability. A developer types one sentence.
The agent walks the repo, extracts business knowledge from Java code,
properties/YAML files, MyBatis mapper XML, SQL/migration files, Spring Batch
jobs, and operational scripts, then writes reviewable skills with confidence
metadata and maintained dependencies.

This skill is the heart of the Skill Generator v2 product. Read it completely
before running it. It is longer than a typical SKILL.md because it contains the
full operating contract for the agent.

---

## How to run this skill

The host AI session (Claude in VS Code/IntelliJ, Copilot Chat, Codex) picks up
this file when a developer types one of the trigger phrases above. The agent
executes the pipeline described here using its own file-read, grep, and bash
tools. The developer reads at two halt gates and types three to five words at
each one.

There is no CLI to install. There are no Python dependencies for the agent
workflow. The four files in `lib/` are structural enforcement utilities that
the agent calls after writing each SKILL.md to catch format errors before
bothering the human.

---

## The biggest risk: silent plausible wrongness

The older Python pipeline failed loudly: validation crashes, malformed output,
obvious contamination. A pure-agent system fails *beautifully* — coherent
feature boundaries that are wrong, persuasive summaries that omit a subsystem,
overconfident architectural reads that the developer won't catch without the
source in front of them.

Every rule in this skill exists to make that failure mode visible. LOW
confidence does not block generation by itself; it marks the generated skill as
`review_required: true` so leads and developers know exactly where to inspect.
Read the halt-gate rules and the evidence-phase template with that risk in mind.

---

## Pipeline overview

```
Step 1    Trigger + pre-flight
Step 2    Crawl (agent walks repo with its own tools)
Step 3    Evidence phase (structured artifact per candidate feature)
── HALT GATE 1 ── Human reviews evidence + plan, may edit grouping
Step 4    Generate (one SKILL.md per planned feature; LOW confidence = review required)
Step 5    Self-validate (deterministic spine via lib/)
Step 6    Link pass (cross-feature dependencies, metadata + both sides updated)
Step 6.5  Catalog generation (.github/skills/catalog.md — discovery layer)
── HALT GATE 2 ── Human reviews .github/skills/, approves commit
Step 7    Commit
```

Steps 3, 5, 6, and 6.5 are the key additions over v1. Step 3 adds auditability
and surfaces the agent's confidence. Step 5 puts the deterministic checker
inside the agent's inner loop so structural errors never reach the human. Step
6 makes feature dependencies durable, so a later change to participant
management can propagate to invoice comparison when invoice comparison depends
on participant data. Step 6.5 produces the discovery catalog AI assistants
read first when matching a developer's natural-language request to a skill.

---

## Step 1 — Trigger and pre-flight

When activated, before doing anything else, confirm:

1. **Working directory.** Ask the developer to confirm the path to the Java
   repository if it is not the current open workspace. Do not proceed with an
   ambiguous path.

2. **Java project check.** Verify the repo contains Java source files.
   Run: `find . -name "*.java" | head -20`. If no `.java` files are found,
   stop and tell the developer this skill targets Java repos only.

3. **Size sanity.** Run: `find . -name "*.java" | wc -l`. Report the class
   count to the developer. If the count is above 300, warn: "This repo is
   larger than v2's tested target of ~300 classes. Proceed with caution —
   results may drift on larger codebases. Type 'proceed' to continue anyway."

4. **Existing skills check.** Check whether `.github/skills/` already
   contains SKILL.md files. If yes, stop and ask the developer whether they
   want to regenerate (replacing all) or update (use skill-updater instead).
   Do not mix generation and update in one run.

If all checks pass, state: "Pre-flight complete. Found N Java classes. Starting
crawl." Then proceed to Step 2.

---

## Step 2 — Crawl rules

The agent walks the repository using its own `Read`, `Grep`, `Glob`, and `Bash`
tools. The goal is to build a mental model of the repo's feature structure before
proposing any grouping.

### What to read

Read these, in order:

1. **Top-level project files:** `pom.xml`, `build.gradle`, `settings.gradle`,
   `settings.gradle.kts`. These reveal the module structure. In a multi-module
   repo, each module is a candidate feature (or group of features).

2. **Package declarations.** Run `grep -r "^package " --include="*.java" . | sort | uniq`
   to map the full package tree. This is your first signal about feature
   boundaries.

3. **Directory structure.** Run `find . -type d | grep -v "target\|build\|\.git"`.
   The directory tree often reveals the feature boundary more clearly than
   package names.

4. **Controller and service interfaces.** `find . -name "*Controller.java" -o -name "*Service.java" | head -40`.
   These are usually the entry points to features.

5. **Entity / model classes.** `find . -name "*Entity.java" -o -name "*Model.java" -o -name "*Domain.java" | head -40`.

6. **Key configuration files.** `find . -name "application*.yml" -o -name "application*.yaml" -o -name "application*.properties"`.
   Read these to understand service names, ports, feature toggles, cache TTLs,
   external dependencies, queue names, and data-source wiring. Do not index CI
   workflow YAML, docker-compose, or monitoring config (Grafana, Prometheus) as
   application features. These are infrastructure files unless application code
   directly reads a key from them.

7. **MyBatis mapper XML and mapper interfaces.** Read `*Mapper.xml`,
   `*Mapper.java`, `mybatis-config.xml`, and mapper-location properties such as
   `mybatis.mapper-locations`. Treat `select`, `insert`, `update`, `delete`,
   `resultMap`, dynamic SQL (`if`, `choose`, `foreach`), joins, stored procedure
   calls, and parameter/result mappings as business evidence. Always connect a
   mapper XML statement back to the Java mapper/service method that uses it.

8. **SQL and migration files.** Read Flyway/Liquibase files, schema DDL, seed
   data, stored procedure scripts, and table/index/constraint definitions.
   These often contain business rules the Java code relies on: status values,
   uniqueness, soft-delete flags, audit columns, reference data, and workflow
   transitions.

9. **Spring Batch applications.** Read `Job`, `Step`, `Tasklet`, `ItemReader`,
   `ItemProcessor`, `ItemWriter`, `JobLauncher`, `JobParameters`, schedulers,
   listeners, batch config XML, and batch metadata/table usage. Batch flows are
   feature behavior, especially when they ingest files, transform records,
   reconcile invoices, deliver reports, or write outbound files.

10. **Operational scripts and scheduled jobs.** Read scripts under `scripts/`,
   `bin/`, `jobs/`, `src/main/resources`, and module-local shell/SQL runners
   when they are referenced by the app or deployment. Treat them as business
   evidence when they load reference data, reconcile files, deliver reports,
   trigger batch jobs, or call feature endpoints.

11. **README.md** if present. This often names the features in plain English
   and is the highest-signal single file in the repo.

### What to skip

Do not read, do not index as candidate features:

- `target/`, `build/`, `.git/`, `.mvn/` directories
- CI workflow files: `.github/workflows/*.yml`, `Jenkinsfile`, `.circleci/`
- Docker/container config: `Dockerfile`, `docker-compose.yml`, `kubernetes/`
- Monitoring config: `*prometheus*.yml`, `*grafana*.json`, `logback*.xml`
- Generated SQL dumps, vendor binaries, or one-off local scripts unless the
  application or deployment references them
- Test-only packages: `src/test/**` (note them, but do not use them to define
  features — tests follow features, not the other way around)
- IDE config: `.idea/`, `.vscode/`, `.classpath`, `.project`

If in doubt about whether something is application code or infrastructure: skip
it for feature analysis and note it in the evidence artifact as "excluded —
infrastructure."

### Cross-contamination prevention

This is the rule that prevents the most common real-repo bugs:

- If two classes share the same simple name across different packages, always
  use the fully qualified name when discussing them in the evidence artifact.
  Never reference `CustomerService` alone if there are three CustomerService
  classes in three modules.

- Nested and inner classes belong to the same feature as their enclosing class.
  Do not list them as separate entities in the evidence artifact.

- A class that appears in both `src/main/java` and `src/test/java` is one class.
  Count it once, in the feature of its main-source package.

---

## Step 3 — Evidence phase

This is the most important step. Do not skip it. Do not combine it with Step 4.

After crawling, produce one **evidence block** per candidate feature before
proposing any grouping or writing any SKILL.md.

The evidence block is the auditable artifact. It tells the human what the agent
saw, what confidence it has, and where it is uncertain. LOW-confidence features
must be flagged explicitly so the human knows where to look hardest. LOW
confidence is a review signal, not an automatic generation stop.

### Evidence block template (required, one per candidate feature)

```
## <feature-id> evidence

Confidence: HIGH | MEDIUM | LOW
Reason:
- <specific observation 1 supporting the confidence level>
- <specific observation 2>
- (optional third observation)

Primary packages:
- <fully qualified package path>

Primary entities + responsibilities:
- <FullyQualified.ClassName> — <one-line responsibility>

Business evidence sources:
- Java: <controllers/services/entities/repos read>
- Config/properties: <keys or files read, or "none observed">
- MyBatis mapper XML: <mapper XML statements/result maps read, or "none observed">
- SQL/migrations: <tables, constraints, seed data, or "none observed">
- Batch/scripts/jobs: <Spring Batch jobs, scripts, schedulers that affect this feature, or "none observed">

Outbound dependencies (features this feature depends on):
- <feature-id> — <why this feature needs it, or "none observed">

Inbound callers (other modules or features that call into this feature):
- <module-id or feature-id>

Excluded classes (looked similar but belong elsewhere):
- <FullyQualified.ClassName> — <reason for exclusion>
```

### Confidence rules

Use these definitions consistently. Do not upgrade confidence to reduce concern
— the human will catch it, and it damages trust.

| Confidence | Definition |
|---|---|
| HIGH | Clear package ownership, single responsibility, no significant overlap with other candidate features |
| MEDIUM | Mostly clear, but some classes could plausibly belong to an adjacent feature, or the package structure is slightly inconsistent |
| LOW | Ambiguous boundary — shared packages, mixed responsibilities, or evidence conflicts with the README description |

LOW-confidence features automatically surface to the human at Halt Gate 1 and in
the generated SKILL.md frontmatter. Use this specific message:

> "FEATURE `<feature-id>` has LOW confidence because: [reasons from evidence block].
> I can still generate it as a review-required draft. Options: (a) generate as
> review-required, (b) merge with another feature, (c) split into two,
> (d) exclude entirely."

If the developer approves the plan generally without resolving a LOW-confidence
feature, generate that feature as a draft with `confidence: LOW` and
`review_required: true`. Do not present LOW-confidence skills as production-ready
or equally trusted. They belong in the final review queue.

### What good evidence looks like

Good evidence is specific. It names real classes with fully qualified paths.
It says why the confidence level was chosen in terms of what the agent actually
read. It lists excluded classes with reasons, not just a count.

### What bad evidence looks like (do not produce this)

```
## payment evidence

Confidence: HIGH
Reason:
- Contains payment-related classes

Primary packages:
- com.example.payment

Primary entities + responsibilities:
- Payment — handles payments
```

This is bad because:
- "Contains payment-related classes" is a tautology, not an observation
- "handles payments" does not describe responsibility precisely
- No excluded classes listed — on any real repo, there are always exclusions
- No inbound callers listed — this is often where the real feature insight lives

A good evidence block for a payment feature on petclinic-style microservices
would look like:

```
## vets-management evidence

Confidence: HIGH
Reason:
- Single module: spring-petclinic-vets-service with one top-level package
- Clear bounded context: exactly three entity classes (Vet, Specialty, VetRepository)
- No cross-contamination: no other module imports from this package directly

Primary packages:
- org.springframework.samples.petclinic.vets.model
- org.springframework.samples.petclinic.vets.web

Primary entities + responsibilities:
- org.springframework.samples.petclinic.vets.model.Vet — aggregate root for vet records
- org.springframework.samples.petclinic.vets.model.Specialty — value object for vet specialty
- org.springframework.samples.petclinic.vets.web.VetResource — REST layer for /vets endpoint

Business evidence sources:
- Java: VetResource, VetRepository, Vet, Specialty
- Config/properties: vets.cache.ttl and vets.cache.heapSize from VetsProperties
- MyBatis mapper XML: none observed
- SQL/migrations: vets and specialties seed/reference tables
- Batch/scripts/jobs: none observed

Outbound dependencies:
- infrastructure-services — config server supplies cache settings; discovery server resolves service name

Inbound callers:
- visits-service (calls /vets/{vetId} for appointment linking)
- api-gateway (routes /vets/* to this service)

Excluded classes:
- org.springframework.samples.petclinic.vets.VetsServiceApplication — bootstrap main, not part of feature behavior
```

---

## Halt Gate 1 — Evidence + plan review

After producing all evidence blocks, present the proposed feature plan to the
developer. Do not produce the plan before all evidence blocks are written.

### Plan format

```
## Proposed feature plan

I found N candidate features based on my crawl. Here is the proposed grouping:

| Feature ID         | Description                     | Confidence | Review required | Classes | Depends on |
|--------------------|---------------------------------|------------|-----------------|---------|------------|
| vets-management    | Vet profiles and specialties    | HIGH       | false           | 6       | infrastructure-services |
| visit-scheduling   | Appointment booking and history | HIGH       | false           | 8       | customers-management |
| owner-registration | Pet owner CRUD + pet management | MEDIUM     | false           | 11      | infrastructure-services |
| shared-support      | Mixed support classes           | LOW        | true            | 4       | owner-registration |

LOW-confidence features flagged for review:
(list any LOW-confidence features here with the four-option prompt from Step 3;
they may still be generated as `review_required: true` drafts)

Do you approve this plan? Reply with one of:
- "yes" — proceed to generation
- feature changes in plain English — I will revise the plan
- "stop" — cancel the run
```

Do not proceed to Step 4 until the developer types "yes", provides grouping
changes, or says to generate LOW-confidence features as review-required drafts.
If the developer gives broad approval, preserve every LOW-confidence flag as
`review_required: true` in the generated SKILL.md.

If the developer requests a change (merge two features, split one, rename), revise
the evidence artifact and plan before proceeding. The revised plan must be
confirmed before generation starts.

---

## Step 4 — Generation rules

Write one SKILL.md per approved feature, following the artifact-3 contract below.

### Artifact-3 contract (required fields, required order)

Every generated SKILL.md must contain these sections in exactly this order:

```yaml
---
skill_id: <feature-id>              # kebab-case, matches directory name
version: 1
last_updated: "<ISO-8601 date>"    # YYYY-MM-DD in quotes
feature_name: "<plain English>"    # What this feature does in 3-5 words
confidence: HIGH | MEDIUM | LOW
review_required: true | false      # true for LOW confidence or human-requested review
primary_packages:
  - <fully.qualified.package>      # At least one; never empty
key_classes:
  - <FullyQualified.ClassName>     # At least one; never empty
depends_on:                        # Optional; omit when none
  - <feature-id-this-feature-calls-or-requires>
depended_on_by:                    # Optional; omit when none
  - <feature-id-that-calls-or-requires-this-feature>

# Discovery + governance fields (all optional but strongly recommended
# at enterprise scale; see "Discovery and ownership metadata" below)
aliases:                           # Optional; natural-language phrases users say
  - <alias 1>
  - <acronym>
business_terms:                    # Optional; domain language for the feature
  - <business term 1>
owner_team:                        # Optional; team identifier (kebab-case
  <team-id>                        # encouraged; aligns with CODEOWNERS)
business_owner:                    # Optional; business stakeholder name or team
  <business owner>
technical_owner:                   # Optional; engineering owner name or team
  <technical owner>
---
```

### Discovery and ownership metadata (optional fields)

These fields are optional in `lib/validate.py` but strongly recommended at
enterprise scale. Generate them when the source evidence supports it; omit
the field entirely when it does not.

| Field | What it is for | How to fill it |
|---|---|---|
| `aliases` | Natural-language phrases or acronyms developers use for this feature | Pull from README, JavaDoc, package-info.java, controller class names, or properties. Examples: `INVCOMP`, `invoice compare`, `invoice comparison report`, `reconciliation`. List 2-6; do not pad. |
| `business_terms` | Domain language a non-engineer would use | Pull from controller endpoints, business-rule comments, validation error messages. Examples: `participant eligibility`, `invoice reconciliation`, `late payment`. |
| `owner_team` | Team identifier matching CODEOWNERS conventions | If `CODEOWNERS` exists, use the team name written there (e.g., `@org/billing-platform` becomes `billing-platform`). If not, leave it for the developer to fill at Halt Gate 1. |
| `business_owner` | Human or team accountable for the business behavior | Pull from README, OWNERS files, JavaDoc `@author`, or leave for the developer. |
| `technical_owner` | Engineering owner accountable for the code | Same sources as `business_owner`. Often the same team. |

If a field cannot be filled from source evidence, leave it out — do not invent
owners or aliases. Surface the gap at Halt Gate 1 so the developer can fill it
or explicitly decline.

The aliases and business_terms fields feed the per-repo `.github/skills/catalog.md`
(see catalog template in `docs/templates/catalog.md`). They are the discovery
layer that lets Copilot/Claude/Codex match a developer's natural-language
request to the right skill.

Then sections in this order:

1. `## Overview` — What this feature does in 2-4 sentences. Plain English.
2. `## Key Classes and Responsibilities` — Table or bullet list. Every class
   in `key_classes` frontmatter must appear here with its responsibility.
3. `## Data Flow` — How data enters, transforms, and exits the feature.
   Must reference real method calls using `ClassName.methodName()` notation.
4. `## Configuration` — Environment variables, Spring Boot properties, or
   config keys that control this feature's behavior. If none: write
   `No runtime configuration for this feature.` (Do not leave this section empty
   and do not write "none found".)
5. `## Integration Points` — Other features, external APIs, or message queues
   this feature calls or receives from. This section must agree with `depends_on`
   and `depended_on_by` frontmatter. If none: write `This feature has no
   integration points with other features.`
6. `## Error Handling` — Optional. Include when the feature has exception
   mapping, retry behavior, fallback behavior, validation failures, or important
   HTTP/status outcomes.
7. `## Business Rules and Edge Cases` — Optional. Include when Java logic,
   MyBatis mapper XML, SQL constraints, seed data, properties, Spring Batch
   steps, or scripts reveal non-obvious rules.
8. `## AI Agent Instructions` — Optional. Include for complex or rule-heavy
   features. Use specific operating rules an AI must follow when editing the
   feature.
9. `## Update Expectations` — What kinds of code changes in this feature would
   require updating this SKILL.md. Be specific: name the sections that change
   when entities are added, configuration changes, MyBatis mapper XML changes,
   SQL changes, Spring Batch job/step behavior changes, script/job behavior
   changes, or new integrations appear.

### Generation rules (non-negotiable)

1. **No PLACEHOLDER text.** Every field must contain real values derived from
   the crawl and evidence phase. If you cannot determine a value with confidence,
   say so explicitly in plain English in that section — do not write a placeholder.

2. **No empty required sections.** If a section genuinely has no content,
   use the fallback text defined above. The fallback text is a real answer,
   not a placeholder.

3. **No Java code fences in SKILL.md files.** Reference classes and methods
   using inline `ClassName.methodName()` notation. Java code blocks belong in
   example files, not in SKILL.md prose.

4. **Fully qualified class names in frontmatter.** The `key_classes` and
   `primary_packages` frontmatter fields must use fully qualified names.

5. **Citation on every factual claim.** If a section says a class does
   something, the class name must appear in that section in the form that
   allows a reader to verify it: `ClassName.methodName()` or
   `com.example.ClassName` depending on context.

6. **Version starts at 1.** The deterministic spine in `lib/validate.py`
   will reject non-integer version values.

7. **last_updated is today's date** in `YYYY-MM-DD` format, in quotes.
   The deterministic spine checks this field.

8. **Confidence metadata is required.** Copy the confidence from the evidence
   block. Set `review_required: true` when confidence is LOW or when the human
   asks for a lead review. MEDIUM confidence may use `review_required: false`
   unless a concrete ambiguity remains.

9. **Dependencies are first-class.** If this feature needs another feature's API,
   tables, files, events, DTOs, config, or reference data, add that feature id to
   `depends_on`. Add the reverse link to the other skill's `depended_on_by`. The
   Integration Points sections on both sides must describe the direction and the
   evidence behind it. Example: `invoice-compare` depends on `participant` when
   invoice comparison reads participant identity, eligibility, account, or
   enrollment data.

10. **Business knowledge must come from source evidence.** Pull rules from Java
    methods, validation annotations, properties/YAML, MyBatis mapper XML,
    SQL constraints/seed data, Spring Batch jobs/steps, and scripts/jobs. If a
    business rule cannot be tied to one of those sources, leave it out or mark it
    as uncertain in the evidence; do not invent it.

11. **No secrets, credentials, or sensitive runtime values in generated skills.**
    When emitting the `## Configuration` section, name the config key but redact
    or omit sensitive values. Mask anything matching common sensitive-value
    patterns: passwords, API keys, tokens, OAuth client secrets, private keys,
    JDBC connection strings with embedded credentials, AWS access keys, signing
    keys, webhook secrets. Customer-identifying reference data (real names,
    emails, account numbers, SSNs) found in seed SQL must also be excluded —
    describe the *shape* of the data, not actual values. Use the literal config
    key name with a redacted placeholder, for example
    `spring.datasource.password = <redacted: secret>` or
    `aws.access-key-id = <redacted>`.

    This rule is the **prevention layer** of a defense-in-depth model.
    `skill-updater` enforces the same rule on updates; `skill-validator`
    provides a safety-net scan for anything that slipped through. Do not
    assume the validator will save you — scrub at write time as if no other
    layer exists.

---

## Step 5 — Self-validation

After writing each SKILL.md, before presenting it to the developer, run the
deterministic spine checks. Do this inside your own turn — do not ask the
developer to run the checks.

### How to run the checks

From the target repo root, run the structural tools from the Skill_Generator
checkout. If the generator repo is not the current working directory, use an
absolute path or set `SKILL_GENERATOR_HOME` first.

```bash
python3 "$SKILL_GENERATOR_HOME/lib/validate.py" .github/skills/<feature-id>/SKILL.md
python3 "$SKILL_GENERATOR_HOME/lib/citation_check.py" .github/skills/<feature-id>/SKILL.md
```

### What to do on failure

If either check fails:

1. Read the error output carefully.
2. Fix the specific failure in the SKILL.md.
3. Re-run the check.
4. If the check fails a second time, stop and tell the developer which check
   failed and why, and ask them how to proceed. Do not attempt a third
   automatic retry — something structural is wrong.

Do not present a SKILL.md to the developer until both checks pass. The
developer should never need to run validation manually on a freshly generated
file.

### What the checks catch (and what they do not)

The deterministic spine catches structural errors: missing frontmatter fields,
wrong field types, wrong section order, missing citations in citation-required
sections, PLACEHOLDER text, empty required sections, Java code fences.

The deterministic spine does **not** catch semantic errors: wrong feature
boundaries, incorrect class responsibilities, missing integration points,
inaccurate data flow descriptions. That is what the evidence phase and Halt
Gate 1 catch. These are complementary layers, not alternatives.

---

## Step 6 — Link pass

After all SKILL.md files pass self-validation, run the dependency/link pass.

Walk each generated SKILL.md and identify integration points where one feature
calls, receives from, shares a data contract with, reads tables owned by, or
uses configuration/events/files produced by another feature that also has a
SKILL.md in this run. For each such pair:

1. Add the called/required feature to the caller's `depends_on` frontmatter.
2. Add the caller to the called feature's `depended_on_by` frontmatter.
3. Confirm the caller's `## Integration Points` section names the dependency
   and explains why it depends on it.
4. Confirm the provider's `## Integration Points` section names the dependent
   feature and explains what it provides.
5. If either side is missing the metadata or prose link, add it.

Both sides of every dependency link must be present before Halt Gate 2. A
one-sided link is a documentation error because update propagation depends on
the graph.

Write the links using feature IDs, not file paths. Example:
`This feature is called by **owner-registration** to resolve pet ownership records.`

After any link-pass edit, re-run `lib/validate.py` and `lib/citation_check.py`
on every edited SKILL.md. Halt Gate 2 must report the post-link validation
result, not the pre-link result.

---

## Step 6.5 — Catalog generation

After the link pass and post-link validation pass, write the per-repo skill
catalog to `.github/skills/catalog.md`.

The catalog is the **discovery layer**. AI assistants (Copilot, Claude, Codex)
read this file first to map a developer's natural-language request to the
right skill, then read the matching `SKILL.md`. Without the catalog, every
host AI has to grep the markdown files itself — which works inconsistently
and burns context every time.

### How to build the catalog

1. Walk every `SKILL.md` file generated in this run.
2. For each skill, collect: `skill_id`, `feature_name`, `confidence`,
   `review_required`, `version`, `last_updated`, `owner_team`,
   `business_owner`, `technical_owner`, `depends_on`, `depended_on_by`,
   `aliases`, `business_terms`.
3. Build the Quick lookup table: one row per entry in `aliases` and
   `business_terms`, mapping the phrase to `[<skill_id>](<skill_id>/SKILL.md)`.
   Use backticks around the phrase. Sort rows alphabetically by phrase.
4. Build the Skills by feature blocks: one block per skill, sorted
   alphabetically by `skill_id`. Include every collected field that has a
   value; omit empty fields entirely. Do not write "none" or "N/A".
5. Copy the "How AI assistants should use this catalog" and "How developers
   should update this catalog" sections from `docs/templates/catalog.md`
   verbatim — these are operating instructions, not generated content.
6. Fill the catalog metadata at the bottom (generator version, skill count,
   generation datetime, repo path, branch name).

### Template

Use `docs/templates/catalog.md` as the structural template. The template
ships with placeholder rows that the generator replaces with real data.

### When a skill has no aliases or business_terms

A skill without aliases or business_terms still appears in the Skills by
feature blocks. It just contributes no rows to the Quick lookup table.
Surface this at Halt Gate 2 as a coverage gap: "skill X has no discovery
phrases; consider adding aliases or business_terms before commit."

### Validation

The catalog is not validated by `lib/validate.py` (it is not a SKILL.md
file). Instead, perform two structural sanity checks before Halt Gate 2:

1. Every `skill_id` in the catalog corresponds to an existing
   `.github/skills/<skill_id>/SKILL.md` file.
2. Every linked path in the catalog (Quick lookup target + Skills by
   feature `depends_on`/`depended_on_by` links) resolves to a real file.

If either check fails, stop and report the inconsistency to the developer.

---

## Halt Gate 2 — Output review before commit

After the link pass, present a summary to the developer:

```
## Generation complete

I wrote N SKILL.md files:
- .github/skills/vets-management/SKILL.md — confidence HIGH, review_required false, passed validation
- .github/skills/visit-scheduling/SKILL.md — confidence HIGH, review_required false, passed validation
- .github/skills/shared-support/SKILL.md — confidence LOW, review_required true, passed validation

Dependency pass: found 3 cross-feature dependencies; frontmatter and both
Integration Points sections updated. Post-link validation passed.

Catalog: .github/skills/catalog.md — N skills indexed; M alias/business-term
phrases mapped. Discovery coverage: K of N skills have at least one alias
or business term (skills with no discovery phrases flagged below).

Review queue:
- .github/skills/shared-support/SKILL.md — LOW confidence; lead review required
- .github/skills/<skill-id>/SKILL.md — no aliases or business_terms; consider adding before commit

Audit log saved to: .github/skills/.skill-gen-audit.md

Ready to commit. Do you approve?
- "yes" — I will run git add + git commit with the message below
- changes in plain English — I will revise before committing
- "stop" — do not commit; leave files in place for manual review

Proposed commit message:
feat: generate feature-based skills for <repo-name>

Generated N SKILL.md files covering <feature-list>.
Evidence artifacts in .github/skills/.skill-gen-audit.md.
Validated with lib/validate.py and lib/citation_check.py.

Co-authored-by: <developer-name>
```

Do not run `git add` or `git commit` until the developer types "yes".

---

## Step 7 — Commit

When the developer approves:

```bash
git add .github/skills/
git commit -m "feat: generate feature-based skills for <repo-name>

Generated N SKILL.md files covering <feature-list>.
Evidence artifacts in .github/skills/.skill-gen-audit.md.
Validated with lib/validate.py and lib/citation_check.py."
```

Use the developer's name in `Co-authored-by` if they provided it at any point
in the session. Otherwise omit the field.

After committing, state: "Done. N skill files committed. Run
`skill-validator` next if you want a semantic review pass."

---

## Audit log format

Write the audit log to `.github/skills/.skill-gen-audit.md` after all SKILL.md
files are written and before Halt Gate 2.

The audit log is a permanent record of the evidence phase. It lets a future
developer (or a future AI session) understand why features were grouped the way
they were without re-reading the source code.

### Audit log template

```markdown
# Skill generation audit log
Generated: <ISO-8601 datetime>
Repo: <repo name and path>
Class count: N
Feature count: M

## Evidence artifacts

<paste all evidence blocks from Step 3 here in feature-id order>

## Plan revisions

<if the developer requested plan changes at Halt Gate 1, document them here.
One bullet per change: what changed and why (use developer's exact words).>

## Validation results

| Feature | validate.py | citation_check.py |
|---------|-------------|-------------------|
| vets-management | PASS | PASS |

## Review queue

| Feature | Confidence | Review required | Reason |
|---------|------------|-----------------|--------|
| shared-support | LOW | true | Mixed package ownership; generated as draft |

## Cross-feature dependencies

| Dependent feature | Provider feature | Evidence | Both sides present? |
|-------------------|------------------|----------|---------------------|
| invoice-compare | participant | Invoice comparison reads participant identity/eligibility before matching invoices | yes |
```

---

## Crawl rules for grouping — what makes a good feature

Use these rules when translating the evidence into a proposed plan. The rules
are in priority order: rule 1 overrides rule 2, and so on.

**Rule 1: Follow module boundaries in multi-module repos.**
If the repo has clearly defined Maven/Gradle modules, treat each module as a
candidate feature. Only merge two modules if their responsibilities are
indistinguishable and their combined class count is below 8.

**Rule 2: Follow package naming in single-module repos.**
If there is a single module, group by the second or third level of the package
hierarchy (e.g., `com.example.billing`, `com.example.customer`). Do not group
by `com.example` alone — that is too coarse. Do not group by
`com.example.billing.internal.util` — that is too fine.

**Rule 3: Treat infrastructure as support context, not business capability.**
Classes that exist only to wire up Spring, configure Hibernate, register beans,
or manage database migrations are not business features. Usually document them
inside the relevant feature's `## Integration Points`. If they are important for
onboarding or startup sequencing, generate a LOW-confidence support skill with
`review_required: true` instead of pretending it is a normal business feature.

**Rule 4: Prefer 5–15 classes per feature.**
A feature with 2 classes is probably a support package that belongs elsewhere.
A feature with 40 classes is probably two features. Use judgment, but if a feature
falls outside 5–15, document the exception in the evidence artifact.

**Rule 5: When uncertain, make it a LOW-confidence feature.**
Do not force a HIGH-confidence assignment. The cost of misclassifying a feature
is higher than the cost of flagging it for human review.

---

## Examples of good and bad grouping behavior

### Good grouping example

Repo: spring-petclinic-microservices (6 microservices)

The agent proposes 6 features, one per microservice:
- `vets-management` (6 classes, HIGH confidence, single module)
- `visit-scheduling` (8 classes, HIGH confidence, single module)
- `owner-registration` (11 classes, HIGH confidence, single module)
- `api-gateway` (4 classes, MEDIUM confidence — small; agent notes this is
  mostly routing config and could be merged into infrastructure)
- `config-server` (2 classes, LOW confidence — agent flags: "This module has
  only 2 classes and exists purely for Spring Cloud config. It may not warrant
  its own SKILL.md. Options: (a) generate as review-required support skill,
  (b) document as infrastructure in api-gateway, (c) skip entirely.")
- `discovery-server` (3 classes, LOW confidence — same reasoning)

The developer sees the LOW-confidence flags and decides: merge `config-server`
and `discovery-server` into a single `infrastructure` feature. The agent revises
the plan, produces one `infrastructure` evidence block, and proceeds.

Result: 5 SKILL.md files. Clean.

### Bad grouping example (do not do this)

Same repo. The agent collapses all 6 microservices into one feature called
`petclinic` and reports HIGH confidence because "all classes are part of the
same project." This is the v1 `doctor` bug: the top-level package heuristic
collapses everything when the agent doesn't actually read the module structure.

This is silent plausible wrongness: the output looks complete, but the entire
point of feature-based skills — that a developer can navigate to the relevant
skill for their feature — is destroyed.

The defense: Rule 1 (follow module boundaries) and the evidence phase (if the
agent actually produces evidence per module, the collapsing error becomes
visible before generation).

### Bad grouping example 2 (cross-contamination)

Multi-module repo where two modules both have a class named `CustomerService`
in different packages. The agent references `CustomerService` without
qualification in both features' evidence blocks. The human cannot tell which is
which.

The defense: the cross-contamination prevention rule in Step 2 (always use
fully qualified names when the same simple name appears in multiple modules)
and the evidence-phase template (which requires fully qualified names in the
"Primary entities" field).

---

## Update expectations (for this SKILL.md itself)

This SKILL.md should be updated when:

- The artifact-3 contract changes (frontmatter fields added, removed, or renamed)
- The halt gate format changes (different options, different confirmation phrases)
- Confidence or review-required behavior changes
- Dependency metadata (`depends_on`, `depended_on_by`) changes
- The deterministic spine changes in a way that affects what `lib/validate.py`
  or `lib/citation_check.py` report
- A new cross-contamination pattern is discovered during real-repo testing
- The evidence-phase template adds or removes required fields
- A new grouping rule is added or an existing rule's priority changes

Do not update this file for implementation details in `lib/`. The SKILL.md
describes the agent's behavior contract, not the implementation of the
structural checks.

---

## Cross-agent portability

This SKILL.md is designed to be executable by any host AI that supports
file-read, grep, and bash tools. The structural outputs (frontmatter, section
order, validation results) are host-independent. The quality of feature
reasoning varies by host.

See `docs/enterprise-agent-selection-guide.md` for the recommended host tier
by workload. For first-run generation on an unknown or older repo, use the
strongest available host (Claude Opus-class or Codex high-reasoning). For
incremental updates and everyday skill consumption, lighter models are fine.
