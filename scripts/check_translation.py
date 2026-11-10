#!/usr/bin/env python3
"""Offline structural review aid; it does not evaluate translation quality.

Exit codes: 0 = no flags, 1 = differences to review, 2 = input/JSON errors.
Text mode compares token counts, not meaning or association with sentences.
JSON mode additionally compares keys, types and non-string values at each path.
"""

from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

LIMITATIONS = (
    "Heuristic structural checks only; no proof of translation accuracy, fluency, "
    "prose completeness, number meaning, or token order/association in text. "
    "Markdown coverage is partial; ICU MessageFormat is not parsed."
)
PLACEHOLDER = re.compile(
    r"\{\{[^{}\n]+\}\}|\$\{[^{}\n]+\}|"
    r"%(?:\([A-Za-z_]\w*\)|\d+\$)?[-+#0 ']*(?:\d+|\*)?(?:\.(?:\d+|\*))?[sdifouxXeEgGc]|"
    r"\{(?:[A-Za-z_][A-Za-z0-9_.-]*|\d+)(?:![rsa])?(?::[^{}\n]+)?\}"
)
URL = re.compile(r"https?://[^\s<>\"'`\u3000-\u303f\uff00-\uffef\u201c\u201d]+")
NUMBER = re.compile(
    r"(?<![A-Za-z0-9_.])[-+−]?(?:[0-9]+(?:[.,][0-9]+)*|[.,][0-9]+)"
    r"(?:[eE][-+]?[0-9]+)?[%‰]?"
)
FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})([^\n]*)$")
INLINE_RUN = re.compile(r"`+")


def _mask(text: str) -> str:
    return "".join("\n" if char == "\n" else " " for char in text)


def _code(text: str) -> tuple[str, Counter[str], Counter[str]]:
    """Extract fences and backtick spans without normalizing protected content."""
    lines = text.splitlines(keepends=True)
    remainder: list[str] = []
    fences: Counter[str] = Counter()
    i = 0
    while i < len(lines):
        opening = FENCE_OPEN.match(lines[i].rstrip("\r\n"))
        if not opening or (opening[1][0] == "`" and "`" in opening[2]):
            remainder.append(lines[i])
            i += 1
            continue
        marker, info = opening.groups()
        closer = re.compile(r"^ {0,3}" + re.escape(marker[0]) + r"{" + str(len(marker)) + r",}[ \t]*$")
        end = i + 1
        while end < len(lines) and not closer.match(lines[end].rstrip("\r\n")):
            end += 1
        closed = end < len(lines)
        body = "".join(lines[i + 1:end]).replace("\r\n", "\n")
        fences[json.dumps([info.strip(), body, closed], ensure_ascii=False)] += 1
        stop = end + 1 if closed else end
        remainder.extend(_mask(line) for line in lines[i:stop])
        i = stop
    visible = "".join(remainder)
    spans: Counter[str] = Counter()
    pieces: list[str] = []
    position = 0
    while match := INLINE_RUN.search(visible, position):
        prefix = visible[:match.start()]
        backslashes = len(prefix) - len(prefix.rstrip("\\"))
        if backslashes % 2:
            pieces.append(visible[position:match.end()])
            position = match.end()
            continue
        closing = None
        for candidate in INLINE_RUN.finditer(visible, match.end()):
            if len(candidate[0]) == len(match[0]):
                closing = candidate
                break
        if closing is None:
            pieces.append(visible[position:match.end()])
            position = match.end()
            continue
        spans[visible[match.end():closing.start()]] += 1
        pieces.append(visible[position:match.start()])
        pieces.append(_mask(visible[match.start():closing.end()]))
        position = closing.end()
    pieces.append(visible[position:])
    return "".join(pieces), fences, spans


def _trim_url(value: str) -> str:
    value = value.rstrip(".,;:!?，。；：！？")
    for opening, closing in (("(", ")"), ("[", "]"), ("{", "}")):
        while value.endswith(closing) and value.count(closing) > value.count(opening):
            value = value[:-1]
    return value


def visible_numbers(text: str) -> Counter[str]:
    visible, _, _ = _code(text)
    visible = URL.sub(" ", visible)
    visible = PLACEHOLDER.sub(" ", visible)
    # A Chinese comma is a prose separator, not a decimal/grouping comma.
    visible = visible.replace("，", " ").replace("−", "-")
    return Counter(NUMBER.findall(unicodedata.normalize("NFKC", visible)))


def collect(text: str, skip_numbers: bool = False, skip_urls: bool = False) -> dict[str, Counter[str]]:
    visible, fences, inline = _code(text)
    result = {
        "fenced_content": fences,
        "inline_code": inline,
        "placeholders": Counter(PLACEHOLDER.findall(visible)),
    }
    if not skip_urls:
        result["urls"] = Counter(_trim_url(value) for value in URL.findall(visible))
    if not skip_numbers:
        result["numbers"] = visible_numbers(visible)
    return result


def compare(source: str, target: str, skip_numbers: bool = False, skip_urls: bool = False) -> list[dict[str, Any]]:
    left, right = collect(source, skip_numbers, skip_urls), collect(target, skip_numbers, skip_urls)
    issues = []
    for category in left:
        missing, added = left[category] - right[category], right[category] - left[category]
        if missing or added:
            def items(values: Counter[str]) -> list[dict[str, Any]]:
                return [{"value": value, "count": count} for value, count in sorted(values.items())]
            issues.append({"category": category, "missing": items(missing), "added": items(added)})
    return issues


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key!r}")
        result[key] = value
    return result


def parse_json(text: str) -> Any:
    def invalid_constant(value: str) -> None:
        raise ValueError(f"Non-standard JSON constant: {value}")
    return json.loads(text, object_pairs_hook=_object, parse_constant=invalid_constant, parse_float=Decimal, parse_int=Decimal)


def compare_json(source: Any, target: Any, skip_numbers: bool = False, skip_urls: bool = False, path: str = "") -> list[dict[str, Any]]:
    """Compare parsed JSON for a task in which string values may be translated."""
    current = path or "/"
    if type(source) is not type(target):
        return [{"category": "json_type", "path": current, "source": type(source).__name__, "translation": type(target).__name__}]
    issues: list[dict[str, Any]] = []
    if isinstance(source, dict):
        missing, added = sorted(source.keys() - target.keys()), sorted(target.keys() - source.keys())
        if missing or added:
            issues.append({"category": "json_keys", "path": current, "missing": missing, "added": added})
        for key in sorted(source.keys() & target.keys()):
            escaped = key.replace("~", "~0").replace("/", "~1")
            issues.extend(compare_json(source[key], target[key], skip_numbers, skip_urls, f"{path}/{escaped}"))
    elif isinstance(source, list):
        if len(source) != len(target):
            issues.append({"category": "json_length", "path": current, "source": len(source), "translation": len(target)})
        for index, (left, right) in enumerate(zip(source, target)):
            issues.extend(compare_json(left, right, skip_numbers, skip_urls, f"{path}/{index}"))
    elif isinstance(source, str):
        for issue in compare(source, target, skip_numbers, skip_urls):
            issues.append({"path": current, **issue})
    elif source != target or (isinstance(source, Decimal) and source.as_tuple() != target.as_tuple()):
        issues.append({"category": "json_value", "path": current, "source": str(source) if isinstance(source, Decimal) else source, "translation": str(target) if isinstance(target, Decimal) else target})
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="UTF-8 source file (optional BOM accepted)")
    parser.add_argument("translation", type=Path, help="UTF-8 translated file")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="JSON mode permits translated string values only")
    parser.add_argument("--json", action="store_true", help="Machine-readable report, including input errors")
    parser.add_argument("--ignore-numbers", action="store_true", help="Skip prose numeric tokens; typed JSON values are still checked")
    parser.add_argument("--ignore-urls", action="store_true", help="Skip prose URL checks; URLs inside protected code are still checked")
    args = parser.parse_args(argv)
    try:
        source = args.source.read_text(encoding="utf-8-sig")
        target = args.translation.read_text(encoding="utf-8-sig")
        if args.format == "json":
            issues = compare_json(parse_json(source), parse_json(target), args.ignore_numbers, args.ignore_urls)
        else:
            issues = compare(source, target, args.ignore_numbers, args.ignore_urls)
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        report = {"schema_version": 1, "status": "input_error", "error": str(exc), "issues": []}
        print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else f"ERROR: {exc}", file=sys.stdout if args.json else sys.stderr)
        return 2
    report = {"schema_version": 1, "status": "review" if issues else "no_flagged_differences", "format": args.format, "limitations": LIMITATIONS, "issues": issues}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("REVIEW NEEDED" if issues else "NO STRUCTURAL DIFFERENCES FLAGGED")
        for issue in issues:
            print(" - " + json.dumps(issue, ensure_ascii=False))
        print(LIMITATIONS)
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
