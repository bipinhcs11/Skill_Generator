---
skill_id: skill-generator
version: 2
last_updated: "2026-05-17"
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

This skill turns a Java repository into a set of feature-based SKILL.md files,
one per coherent domain. A developer types one sentence. The agent walks the
repo, produces auditable evidence per candidate domain, halts for human review,
then generates and self-validates the skill files.

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

The v1 Python pipeline failed loudly: validation crashes, malformed output,
obvious contamination. A pure-agent system fails *beautifully* — coherent
domain boundaries that are wrong, persuasive summaries that omit a subsystem,
overconfident architectural reads that the developer won't catch without the
source in front of them.

Every rule in this skill exists to make that failure mode visible before the
human approves. Read the halt-gate rules and the evidence-phase template with
that risk in mind.

---

## Pipeline overview

```
Step 1  Trigger + pre-flight
Step 2  Crawl (agent walks repo with its own tools)
Step 3  Evidence phase (structured artifact per candidate domain)
── HALT GATE 1 ── Human reviews evidence + plan, approves/edits/rejects
Step 4  Generate (one SKILL.md per approved domain)
Step 5  Self-validate (deterministic spine via lib/)
Step 6  Link pass (cross-domain dependencies, both sides updated)
── HALT GATE 2 ── Human reviews .github/skills/, approves commit
Step 7  Commit
```

Steps 3 and 5 are the key additions over v1. Step 3 adds auditability and
surfaces the agent's confidence before any SKILL.md is written. Step 5 puts
the deterministic checker inside the agent's inner loop so structural errors
never reach the human.

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
tools. The goal is to build a mental model of the repo's domain structure before
proposing any grouping.

### What to read

Read these, in order:

1. **Top-level project files:** `pom.xml`, `build.gradle`, `settings.gradle`,
   `settings.gradle.kts`. These reveal the module structure. In a multi-module
   repo, each module is a candidate domain (or group of domains).

2. **Package declarations.** Run `grep -r "^package " --include="*.java" . | sort | uniq`
   to map the full package tree. This is your first signal about domain
   boundaries.

3. **Directory structure.** Run `find . -type d | grep -v "target\|build\|\.git"`.
   The directory tree often reveals the domain boundary more clearly than
   package names.

4. **Controller and service interfaces.** `find . -name "*Controller.java" -o -name "*Service.java" | head -40`.
   These are usually the entry points to domains.

5. **Entity / domain model classes.** `find . -name "*Entity.java" -o -name "*Model.java" -o -name "*Domain.java" | head -40`.

6. **Key configuration files.** `find . -name "application*.yml" -o -name "application*.properties"`.
   Read these to understand service names, ports, and external dependencies.
   Do not index CI workflow YAML, docker-compose, or monitoring config
   (Grafana, Prometheus) as application domains. These are infrastructure files.

7. **README.md** if present. This often names the domains in plain English
   and is the highest-signal single file in the repo.

### What to skip

Do not read, do not index as candidate domains:

- `target/`, `build/`, `.git/`, `.mvn/` directories
- CI workflow files: `.github/workflows/*.yml`, `Jenkinsfile`, `.circleci/`
- Docker/container config: `Dockerfile`, `docker-compose.yml`, `kubernetes/`
- Monitoring config: `*prometheus*.yml`, `*grafana*.json`, `logback*.xml`
- Test-only packages: `src/test/**` (note them, but do not use them to define
  domains — tests follow domains, not the other way around)
- IDE config: `.idea/`, `.vscode/`, `.classpath`, `.project`

If in doubt about whether something is application code or infrastructure: skip
it for domain analysis and note it in the evidence artifact as "excluded —
infrastructure."

### Cross-contamination prevention

This is the rule that prevents the most common real-repo bugs:

- If two classes share the same simple name across different packages, always
  use the fully qualified name when discussing them in the evidence artifact.
  Never reference `CustomerService` alone if there are three CustomerService
  classes in three modules.

- Nested and inner classes belong to the same domain as their enclosing class.
  Do not list them as separate entities in the evidence artifact.

- A class that appears in both `src/main/java` and `src/test/java` is one class.
  Count it once, in the domain of its main-source package.

---

## Step 3 — Evidence phase

This is the most important step. Do not skip it. Do not combine it with Step 4.

After crawling, produce one **evidence block** per candidate domain before
proposing any grouping or writing any SKILL.md.

The evidence block is the auditable artifact. It tells the human what the agent
saw, what confidence it has, and where it is uncertain. LOW-confidence domains
must be flagged explicitly so the human knows where to look hardest.

### Evidence block template (required, one per candidate domain)

```
## <domain-id> evidence

Confidence: HIGH | MEDIUM | LOW
Reason:
- <specific observation 1 supporting the confidence level>
- <specific observation 2>
- (optional third observation)

Primary packages:
- <fully qualified package path>

Primary entities + responsibilities:
- <FullyQualified.ClassName> — <one-line responsibility>

Inbound callers (other modules or domains that call into this domain):
- <module-id or domain-id>

Excluded classes (looked similar but belong elsewhere):
- <FullyQualified.ClassName> — <reason for exclusion>
```

### Confidence rules

Use these definitions consistently. Do not upgrade confidence to reduce concern
— the human will catch it, and it damages trust.

| Confidence | Definition |
|---|---|
| HIGH | Clear package ownership, single responsibility, no significant overlap with other candidate domains |
| MEDIUM | Mostly clear, but some classes could plausibly belong to an adjacent domain, or the package structure is slightly inconsistent |
| LOW | Ambiguous boundary — shared packages, mixed responsibilities, or evidence conflicts with the README description |

LOW-confidence domains automatically surface to the human at Halt Gate 1 with
this specific message:

> "DOMAIN `<domain-id>` has LOW confidence because: [reasons from evidence block].
> Please confirm whether this grouping is correct or override it before I proceed
> to generation. Options: (a) confirm as-is, (b) merge with another domain,
> (c) split into two, (d) exclude entirely."

Do not generate a SKILL.md for a LOW-confidence domain until the human has
explicitly chosen one of the four options above.

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
- No inbound callers listed — this is often where the real domain insight lives

A good evidence block for a payment domain on petclinic-style microservices
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

Inbound callers:
- visits-service (calls /vets/{vetId} for appointment linking)
- api-gateway (routes /vets/* to this service)

Excluded classes:
- org.springframework.samples.petclinic.vets.VetsServiceApplication — bootstrap main, not part of domain logic
```

---

## Halt Gate 1 — Evidence + plan review

After producing all evidence blocks, present the proposed domain plan to the
developer. Do not produce the plan before all evidence blocks are written.

### Plan format

```
## Proposed domain plan

I found N candidate domains based on my crawl. Here is the proposed grouping:

| Domain ID         | Description                        | Confidence | Classes |
|-------------------|------------------------------------|------------|---------|
| vets-management   | Vet profiles and specialties       | HIGH       | 6       |
| visit-scheduling  | Appointment booking and history    | HIGH       | 8       |
| owner-registration| Pet owner CRUD + pet management    | MEDIUM     | 11      |

LOW-confidence domains flagged for review:
(list any LOW-confidence domains here with the four-option prompt from Step 3)

Do you approve this plan? Reply with one of:
- "yes" — proceed to generation
- domain changes in plain English — I will revise the plan
- "stop" — cancel the run
```

Do not proceed to Step 4 until the developer types "yes" or a revision that
resolves all LOW-confidence flags.

If the developer requests a change (merge two domains, split one, rename), revise
the evidence artifact and plan before proceeding. The revised plan must be
confirmed before generation starts.

---

## Step 4 — Generation rules

Write one SKILL.md per approved domain, following the artifact-3 contract below.

### Artifact-3 contract (required fields, required order)

Every generated SKILL.md must contain these sections in exactly this order:

```yaml
---
skill_id: <domain-id>              # kebab-case, matches directory name
version: 1
last_updated: "<ISO-8601 date>"    # YYYY-MM-DD in quotes
feature_name: "<plain English>"    # What this domain does in 3-5 words
primary_packages:
  - <fully.qualified.package>      # At least one; never empty
key_classes:
  - <FullyQualified.ClassName>     # At least one; never empty
---
```

Then sections in this order:

1. `## Overview` — What this domain does in 2-4 sentences. Plain English.
2. `## Key Classes and Responsibilities` — Table or bullet list. Every class
   in `key_classes` frontmatter must appear here with its responsibility.
3. `## Data Flow` — How data enters, transforms, and exits the domain.
   Must reference real method calls using `ClassName.methodName()` notation.
4. `## Configuration` — Environment variables, Spring Boot properties, or
   config keys that control this domain's behavior. If none: write
   `No runtime configuration for this domain.` (Do not leave this section empty
   and do not write "none found".)
5. `## Integration Points` — Other domains, external APIs, or message queues
   this domain calls or receives from. If none: write
   `This domain has no integration points with other features.`
6. `## Update Expectations` — What kinds of code changes in this domain would
   require updating this SKILL.md. Be specific: name the sections that change
   when entities are added, configuration changes, or new integrations appear.

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

---

## Step 5 — Self-validation

After writing each SKILL.md, before presenting it to the developer, run the
deterministic spine checks. Do this inside your own turn — do not ask the
developer to run the checks.

### How to run the checks

From the repo root, run:

```bash
python3 lib/validate.py .github/skills/<domain-id>/SKILL.md
python3 lib/citation_check.py .github/skills/<domain-id>/SKILL.md
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

The deterministic spine does **not** catch semantic errors: wrong domain
boundaries, incorrect class responsibilities, missing integration points,
inaccurate data flow descriptions. That is what the evidence phase and Halt
Gate 1 catch. These are complementary layers, not alternatives.

---

## Step 6 — Link pass

After all SKILL.md files pass self-validation, run the link pass.

Walk each generated SKILL.md and identify integration points where one domain
calls or receives from another domain that also has a SKILL.md in this run.
For each such pair:

1. Confirm the calling domain's `## Integration Points` section names the
   called domain.
2. Confirm the called domain's `## Integration Points` section names the
   calling domain.
3. If either side is missing the link, add it.

Both sides of every integration link must be present before Halt Gate 2.
A one-sided link is a documentation error.

Write the links using domain IDs, not file paths. Example:
`This domain is called by **owner-registration** to resolve pet ownership records.`

---

## Halt Gate 2 — Output review before commit

After the link pass, present a summary to the developer:

```
## Generation complete

I wrote N SKILL.md files:
- .github/skills/vets-management/SKILL.md — passed validation
- .github/skills/visit-scheduling/SKILL.md — passed validation
- .github/skills/owner-registration/SKILL.md — passed validation

Link pass: found 3 cross-domain connections; both sides updated.

Audit log saved to: .github/skills/.skill-gen-audit.md

Ready to commit. Do you approve?
- "yes" — I will run git add + git commit with the message below
- changes in plain English — I will revise before committing
- "stop" — do not commit; leave files in place for manual review

Proposed commit message:
feat: generate feature-based skills for <repo-name>

Generated N SKILL.md files covering <domain-list>.
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

Generated N SKILL.md files covering <domain-list>.
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
developer (or a future AI session) understand why domains were grouped the way
they were without re-reading the source code.

### Audit log template

```markdown
# Skill generation audit log
Generated: <ISO-8601 datetime>
Repo: <repo name and path>
Class count: N
Domain count: M

## Evidence artifacts

<paste all evidence blocks from Step 3 here in domain-id order>

## Plan revisions

<if the developer requested plan changes at Halt Gate 1, document them here.
One bullet per change: what changed and why (use developer's exact words).>

## Validation results

| Domain | validate.py | citation_check.py |
|--------|-------------|-------------------|
| vets-management | PASS | PASS |

## Cross-domain links

| Caller       | Called          | Link direction | Both sides present? |
|--------------|-----------------|----------------|---------------------|
| owner-reg    | vets-management | calls → | yes |
```

---

## Crawl rules for grouping — what makes a good domain

Use these rules when translating the evidence into a proposed plan. The rules
are in priority order: rule 1 overrides rule 2, and so on.

**Rule 1: Follow module boundaries in multi-module repos.**
If the repo has clearly defined Maven/Gradle modules, treat each module as a
candidate domain. Only merge two modules if their responsibilities are
indistinguishable and their combined class count is below 8.

**Rule 2: Follow package naming in single-module repos.**
If there is a single module, group by the second or third level of the package
hierarchy (e.g., `com.example.billing`, `com.example.customer`). Do not group
by `com.example` alone — that is too coarse. Do not group by
`com.example.billing.internal.util` — that is too fine.

**Rule 3: Do not create a domain for infrastructure.**
Classes that exist only to wire up Spring, configure Hibernate, register beans,
or manage database migrations are not a domain. Group them into the most
relevant domain's `## Integration Points` section as "shared infrastructure".

**Rule 4: Prefer 5–15 classes per domain.**
A domain with 2 classes is probably a support package that belongs elsewhere.
A domain with 40 classes is probably two domains. Use judgment, but if a domain
falls outside 5–15, document the exception in the evidence artifact.

**Rule 5: When uncertain, make it a LOW-confidence domain.**
Do not force a HIGH-confidence assignment. The cost of misclassifying a domain
is higher than the cost of flagging it for human review.

---

## Examples of good and bad grouping behavior

### Good grouping example

Repo: spring-petclinic-microservices (6 microservices)

The agent proposes 6 domains, one per microservice:
- `vets-management` (6 classes, HIGH confidence, single module)
- `visit-scheduling` (8 classes, HIGH confidence, single module)
- `owner-registration` (11 classes, HIGH confidence, single module)
- `api-gateway` (4 classes, MEDIUM confidence — small; agent notes this is
  mostly routing config and could be merged into infrastructure)
- `config-server` (2 classes, LOW confidence — agent flags: "This module has
  only 2 classes and exists purely for Spring Cloud config. It may not warrant
  its own SKILL.md. Options: (a) keep as-is, (b) document as infrastructure
  in api-gateway, (c) skip entirely.")
- `discovery-server` (3 classes, LOW confidence — same reasoning)

The developer sees the LOW-confidence flags and decides: merge `config-server`
and `discovery-server` into a single `infrastructure` domain. The agent revises
the plan, produces one `infrastructure` evidence block, and proceeds.

Result: 5 SKILL.md files. Clean.

### Bad grouping example (do not do this)

Same repo. The agent collapses all 6 microservices into one domain called
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
qualification in both domains' evidence blocks. The human cannot tell which is
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
order, validation results) are host-independent. The quality of domain
reasoning varies by host.

See `docs/enterprise-agent-selection-guide.md` for the recommended host tier
by workload. For first-run generation on an unknown or legacy repo, use the
strongest available host (Claude Opus-class or Codex high-reasoning). For
incremental updates and everyday skill consumption, lighter models are fine.
