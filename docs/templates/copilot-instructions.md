# Copilot Instructions for Feature Skills

Before answering feature questions or editing application code, check whether
the target repo contains `.github/skills/`.

When a user asks about a feature:

1. **Look up the right skill in `.github/skills/catalog.md`** first. The
   catalog maps natural-language phrases, acronyms, and business terms (e.g.,
   `INVCOMP`, `invoice comparison report`, `participant eligibility`) to
   skill IDs. If a match is found, use the linked path.
2. Read the matching `.github/skills/<feature-id>/SKILL.md` fully.
3. Read any feature skills listed in `depends_on`.
4. Use the skill's `key_classes`, `primary_packages`, `Integration Points`, and
   `Update Expectations` to decide which source files matter.
5. Verify behavior against source before changing Java, config, MyBatis XML,
   SQL/migrations, Spring Batch, or scripts.
6. Do not invent feature behavior that is not backed by the skill or source.
7. If the catalog has no match and no `SKILL.md` covers what the user is
   asking about, say so — do not silently fall back to ungrounded code reading.

When a code change may alter behavior captured in a skill, tell the developer to
run Skill Generator v2's `skill-tracker` first. Run `skill-updater` only for the
approved impacted skills.
