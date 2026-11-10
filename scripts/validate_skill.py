#!/usr/bin/env python3
"""Offline project validator, not an official Agent Skills/YAML conformance tool.

Supports the project's YAML subset: string scalars, simple block scalars and a
single nested string mapping (metadata). Unsupported YAML fails explicitly.
Checks local Skill/reference links and optional behavioral fixture schemas.
Exit codes: 0 = valid, 1 = validation findings, 2 = inaccessible input root.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LOCAL_LINK = re.compile(r"\[[^\]\n]*\]\((<[^>]+>|[^\s)]+)(?:\s+[\"'][^\n]*?[\"'])?\)")
REQUIRED_CASE = {"id", "language", "category", "source", "expected", "notes"}
FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}


def _scalar(raw: str) -> str:
    if raw.startswith('"'):
        try:
            value, end = json.JSONDecoder().raw_decode(raw)
        except ValueError as exc:
            raise ValueError("Invalid double-quoted string; use JSON-compatible escapes") from exc
        remainder = raw[end:].strip()
        if not isinstance(value, str) or (remainder and not remainder.startswith("#")):
            raise ValueError("Invalid string scalar")
        return value
    if raw.startswith("'"):
        match = re.fullmatch(r"'((?:[^']|'')*)'\s*(?:#.*)?", raw)
        if not match:
            raise ValueError("Unclosed single-quoted scalar")
        return match[1].replace("''", "'")
    raw = re.split(r"\s+#", raw, maxsplit=1)[0].rstrip()
    if not raw or raw[0] in "[{@&*!>|" or raw in ("null", "Null", "NULL", "~", "true", "false", "True", "False"):
        raise ValueError("Expected a string scalar; quote YAML-special values")
    if re.fullmatch(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", raw):
        raise ValueError("Numeric metadata values must be quoted strings")
    if ": " in raw:
        raise ValueError("Quote scalars containing ': '")
    return raw


def parse_frontmatter(text: str) -> dict[str, object]:
    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("SKILL.md must begin with YAML frontmatter ('---')")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("Missing closing frontmatter '---'") from exc
    values: dict[str, object] = {}
    index = 1
    while index < end:
        line = lines[index]
        index += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"([a-z][a-z0-9_-]*):(?:[ \t]+(.*))?", line)
        if not match:
            raise ValueError(f"Unsupported frontmatter syntax on line {index}")
        key, raw = match[1], (match[2] or "").strip()
        if key in values:
            raise ValueError(f"Duplicate frontmatter key: {key}")
        if key == "metadata" and not raw:
            mapping: dict[str, str] = {}
            while index < end and (lines[index].startswith("  ") or not lines[index].strip()):
                nested = lines[index]
                index += 1
                if not nested.strip() or nested.lstrip().startswith("#"):
                    continue
                child = re.fullmatch(r"  ([A-Za-z0-9_-]+):[ \t]+(.+)", nested)
                if not child:
                    raise ValueError("metadata must contain two-space-indented string fields")
                if child[1] in mapping:
                    raise ValueError(f"Duplicate metadata key: {child[1]}")
                mapping[child[1]] = _scalar(child[2].strip())
            values[key] = mapping
        elif raw in ("|", "|-", "|+", ">", ">-", ">+"):
            block: list[str] = []
            while index < end and (lines[index].startswith("  ") or not lines[index].strip()):
                block.append(lines[index][2:] if lines[index].startswith("  ") else "")
                index += 1
            if not block:
                raise ValueError(f"Empty block scalar: {key}")
            # Fold ordinary lines; preserve paragraph breaks and more-indented lines.
            if raw.startswith(">"):
                folded = block[0]
                for previous, following in zip(block, block[1:]):
                    folded += (" " if previous and following and not previous.startswith(" ") and not following.startswith(" ") else "\n") + following
                value = folded
            else:
                value = "\n".join(block)
            values[key] = value.rstrip("\n") if raw.endswith("-") else value + "\n"
        else:
            values[key] = _scalar(raw)
    return values


def _check_links(root: Path, file: Path, content: str) -> list[str]:
    issues = []
    # Ignore fenced examples; this is a Markdown-link check, not a full parser.
    visible = re.sub(r"(?ms)^ {0,3}(`{3,}|~{3,})[^\n]*\n.*?^ {0,3}\1[ \t]*$", "", content)
    for original in LOCAL_LINK.findall(visible):
        link = original.strip("<>")
        parsed = urlsplit(link)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        relative = unquote(parsed.path)
        target = (file.parent / relative).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            issues.append(f"{file.relative_to(root)}: broken/unsafe local link: {link}")
    return issues


def _check_cases(file: Path) -> list[str]:
    issues = []
    try:
        cases = json.loads(file.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        return [f"Invalid tests/cases.json: {exc}"]
    if not isinstance(cases, list) or not cases:
        return ["tests/cases.json must be a nonempty JSON array"]
    seen: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            issues.append(f"Case #{index} must be an object")
            continue
        missing = REQUIRED_CASE - case.keys()
        if missing:
            issues.append(f"Case #{index} missing: {', '.join(sorted(missing))}")
        for field in REQUIRED_CASE | {"request", "context"}:
            if field in case and (not isinstance(case[field], str) or not case[field].strip()):
                issues.append(f"Case #{index} field {field} must be a nonempty string")
        case_id = case.get("id")
        if isinstance(case_id, str):
            if case_id in seen:
                issues.append(f"Duplicate case id: {case_id}")
            seen.add(case_id)
        if "must_preserve" in case and (not isinstance(case["must_preserve"], list) or not all(isinstance(item, str) and item for item in case["must_preserve"])):
            issues.append(f"Case #{index} must_preserve must be a list of nonempty strings")
    return issues


def validate(root: Path) -> list[str]:
    root = root.resolve()
    skill = root / "SKILL.md"
    if not skill.is_file():
        return [f"Missing {skill}"]
    try:
        content = skill.read_text(encoding="utf-8-sig")
        metadata = parse_frontmatter(content)
    except (OSError, UnicodeError, ValueError) as exc:
        return [str(exc)]
    issues: list[str] = []
    for key in metadata.keys() - FIELDS:
        issues.append(f"Unsupported frontmatter field: {key}")
    name, description = metadata.get("name", ""), metadata.get("description", "")
    if not isinstance(name, str) or not NAME.fullmatch(name) or len(name) > 64:
        issues.append("Invalid name: lowercase letters/digits with single hyphens, maximum 64 characters")
    if name != root.name:
        issues.append(f"Frontmatter name {name!r} does not match directory {root.name!r}")
    if not isinstance(description, str) or not 1 <= len(description.strip()) <= 1024:
        issues.append("Invalid description: nonempty string, maximum 1024 characters")
    compatibility = metadata.get("compatibility", "")
    if not isinstance(compatibility, str) or len(compatibility) > 500:
        issues.append("Invalid compatibility: string, maximum 500 characters")
    if "metadata" in metadata and not isinstance(metadata["metadata"], dict):
        issues.append("metadata must be a mapping of strings")
    if len(content.splitlines()) > 500:
        issues.append("SKILL.md exceeds the project's 500-line limit; move detail to references")
    files = [skill, *sorted((root / "references").glob("**/*.md"))]
    for file in files:
        if not file.resolve().is_relative_to(root):
            issues.append(f"Resource escapes the package: {file}")
            continue
        try:
            issues.extend(_check_links(root, file, file.read_text(encoding="utf-8-sig")))
        except (OSError, UnicodeError, ValueError) as exc:
            issues.append(f"Cannot validate {file.name}: {exc}")
    fixture = root / "tests" / "cases.json"
    if fixture.is_file():
        issues.extend(_check_cases(fixture))
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir", nargs="?", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--json", action="store_true", help="Machine-readable report")
    args = parser.parse_args(argv)
    root = args.skill_dir.resolve()
    if not root.is_dir():
        report = {"schema_version": 1, "status": "input_error", "issues": [f"Not a directory: {root}"]}
        code = 2
    else:
        issues = validate(root)
        report = {"schema_version": 1, "status": "fail" if issues else "pass", "issues": issues}
        code = 1 if issues else 0
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"{report['status'].upper()}: project package checks (not translation quality)")
        for issue in report["issues"]:
            print(f" - {issue}")
    return code


if __name__ == "__main__":
    sys.exit(main())
