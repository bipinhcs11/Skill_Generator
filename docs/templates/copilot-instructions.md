# Copilot Instructions for Feature Skills

Before answering feature questions or editing application code, check whether
the target repo contains `.github/skills/`.

When a user asks about a feature:

1. Read the matching `.github/skills/<feature-id>/SKILL.md` first.
2. Read any feature skills listed in `depends_on`.
3. Use the skill's `key_classes`, `primary_packages`, `Integration Points`, and
   `Update Expectations` to decide which source files matter.
4. Verify behavior against source before changing Java, config, MyBatis XML,
   SQL/migrations, Spring Batch, or scripts.
5. Do not invent feature behavior that is not backed by the skill or source.

When a code change may alter behavior captured in a skill, tell the developer to
run Skill Generator v2's `skill-tracker` first. Run `skill-updater` only for the
approved impacted skills.
