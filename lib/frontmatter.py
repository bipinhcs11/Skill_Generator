"""
lib/frontmatter.py — Parse and serialize SKILL.md YAML frontmatter.

Architectural boundary: handles edge cases (--- collisions, list items with
colons, bare keys) so validate.py gets a clean dict. Does not validate content.

Why this exists: naive split-on-'---' parsing breaks on quoted strings, and
PyYAML is not in scope (stdlib-only constraint).
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field

_LIST_ITEM_RE = re.compile(r'^\s{2,}- (.+)$')
_KEY_VALUE_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$')


@dataclass
class ParseResult:
    frontmatter: dict
    body: str
    errors: list[str] = field(default_factory=list)


def parse(text: str) -> ParseResult:
    """Parse SKILL.md text. Never raises — errors go into ParseResult.errors."""
    lines = text.splitlines()
    fences = [i for i, l in enumerate(lines) if l.strip() == "---"]
    if len(fences) < 2:
        return ParseResult({}, text, ["Could not find two '---' delimiters"])

    fm_lines = lines[fences[0] + 1: fences[1]]
    body = "\n".join(lines[fences[1] + 1:])

    fm: dict = {}
    current_key: str | None = None
    current_list: list | None = None

    for line in fm_lines:
        list_m = _LIST_ITEM_RE.match(line)
        kv_m = _KEY_VALUE_RE.match(line)
        if list_m and current_list is not None:
            current_list.append(list_m.group(1).strip())
        elif kv_m:
            if current_key and current_list is not None:
                fm[current_key] = current_list
            current_key = kv_m.group(1)
            val = kv_m.group(2).strip().strip('"').strip("'")
            if val:
                fm[current_key] = val
                current_list = None
            else:
                current_list = []
                fm[current_key] = current_list

    if current_key and current_list is not None:
        fm[current_key] = current_list

    return ParseResult(fm, body)


def serialize(frontmatter: dict, body: str) -> str:
    """Serialize frontmatter dict + body back to SKILL.md string."""
    lines = ["---"]
    for key, value in frontmatter.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        elif isinstance(value, int):
            lines.append(f"{key}: {value}")
        else:
            safe = str(value)
            if any(c in safe for c in (':', '#', '[', ']', '{', '}')):
                safe = f'"{safe}"'
            lines.append(f"{key}: {safe}")
    lines.append("---")
    return "\n".join(lines) + "\n" + body


def bump_version(text: str) -> str:
    """Increment the integer version field. Used by skill-updater after a successful update."""
    result = parse(text)
    if result.errors:
        raise ValueError(f"Cannot bump version: {result.errors}")
    fm = result.frontmatter
    try:
        fm["version"] = int(fm.get("version", 0)) + 1
    except (ValueError, TypeError) as e:
        raise ValueError(f"version is not an integer: {e}") from e
    return serialize(fm, result.body)
