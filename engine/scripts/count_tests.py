#!/usr/bin/env python3
"""Count test cases from the checked-in Python and Vitest source trees."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

PYTHON_TEST_RE = re.compile(r"^\s*(?:async\s+)?def\s+(test_[A-Za-z0-9_]+)\s*\(", re.MULTILINE)
JS_TEST_RE = re.compile(r"\b(?:it|test)(?:\.[A-Za-z0-9_]+)*\s*\(\s*([\"'`])", re.MULTILINE)


def count_python_tests(root: Path) -> dict[str, object]:
    files = sorted(path for path in root.rglob("test_*.py") if path.is_file())
    cases = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for match in PYTHON_TEST_RE.finditer(text):
            cases.append({"file": str(path.relative_to(root)), "name": match.group(1)})
    return {"files": len(files), "cases": len(cases), "items": cases}


def count_vitest_tests(root: Path) -> dict[str, object]:
    files = sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and not {".git", "node_modules", "dist", "build"}.intersection(path.parts)
        and re.search(r"\.(test|spec)\.(?:ts|tsx|js|jsx|mjs|cjs)$", path.name)
    )
    cases = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for match in JS_TEST_RE.finditer(text):
            cases.append({"file": str(path.relative_to(root)), "name": "anonymous"})
    return {"files": len(files), "cases": len(cases), "items": cases}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python-root", type=Path, default=Path("engine/tests"))
    parser.add_argument("--vitest-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = {
        "python": count_python_tests(args.python_root),
        "vitest": count_vitest_tests(args.vitest_root),
    }
    result["total"] = result["python"]["cases"] + result["vitest"]["cases"]
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
