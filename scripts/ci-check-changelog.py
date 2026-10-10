#!/usr/bin/env python3
"""CI check: require a changelog entry when package source files are modified.

Repositories in the HyperSpy organisation use towncrier for changelog
management: every user-facing change must include a fragment file in the
towncrier ``directory`` (``upcoming_changes/`` by default).  This script
fails the CI job when a pull request modifies Python source under the
configured source directories (excluding tests) without an accompanying
changelog fragment.

Usage (in CI)::

    ci-check-changelog.py [--pyproject PATH] [--source-dir DIR ...]
                           [--changelog-dir DIR] BASE HEAD

``BASE`` and ``HEAD`` are the pull-request base and head commits.  The
changed files are computed with the THREE-dot ``BASE...HEAD`` form so only
changes reachable from the pull request are counted - changes that exist
only on the base branch never trigger a failure.  Exit codes: 0 clean,
1 changelog entry missing, 2 usage or configuration error.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

EXIT_OK = 0
EXIT_MISSING = 1
EXIT_ERROR = 2

DEFAULT_CHANGELOG_DIR = "upcoming_changes"
DEFAULT_TYPES = [
    "new",
    "enhancements",
    "bugfix",
    "api",
    "deprecation",
    "doc",
    "maintenance",
]


def _load_towncrier(pyproject: str) -> dict[str, Any] | None:
    """Return the ``[tool.towncrier]`` table, or None when unreadable."""
    try:
        import tomllib
    except ImportError:  # pragma: no cover - exercised on Python < 3.11
        print(
            "ERROR: Python >= 3.11 required for --pyproject parsing;"
            " pass --source-dir and --changelog-dir explicitly",
            file=sys.stderr,
        )
        return None
    path = Path(pyproject)
    if not path.is_file():
        print(f"ERROR: {path} not found", file=sys.stderr)
        return None
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return data.get("tool", {}).get("towncrier", {})


def _resolve_config(
    pyproject: str,
    source_dirs: list[str],
    changelog_dir: str | None,
) -> tuple[list[str], str, list[str]] | None:
    """Resolve (source_dirs, changelog_dir, fragment_types) from args + towncrier."""
    config: dict[str, Any] | None = {}
    if pyproject and Path(pyproject).is_file():
        config = _load_towncrier(pyproject)
        if config is None:  # ImportError already reported
            return None
    types = [
        entry["directory"]
        for entry in config.get("type", [])
        if isinstance(entry, dict) and entry.get("directory")
    ] or DEFAULT_TYPES
    if changelog_dir:
        resolved_changelog = changelog_dir
    elif config:
        resolved_changelog = str(config.get("directory", DEFAULT_CHANGELOG_DIR))
    else:
        resolved_changelog = DEFAULT_CHANGELOG_DIR
    resolved_changelog = resolved_changelog.rstrip("/")
    if source_dirs:
        return source_dirs, resolved_changelog, types
    package = config.get("package")
    package_dir = config.get("package_dir")
    if not package and not package_dir:
        print(
            "ERROR: Cannot derive source directories; pass --source-dir",
            file=sys.stderr,
        )
        return None
    if package and package_dir:
        # Nested layout: package lives under package_dir.  Equal names are a
        # legitimate nested layout (pkg/pkg), so no equality shortcut.
        return [str(package_dir) + "/" + str(package)], resolved_changelog, types
    return [str(package or package_dir)], resolved_changelog, types


def _changed_files(base: str, head: str) -> list[tuple[str, str]]:
    """Return (status, path) pairs for BASE...HEAD, exit 2 when unreachable."""
    probe = subprocess.run(
        ["git", "cat-file", "-e", f"{base}^{{commit}}"],
        capture_output=True,
        check=False,
    )
    if probe.returncode != 0:
        print(
            "ERROR: BASE commit not reachable - checkout with fetch-depth: 0",
            file=sys.stderr,
        )
        sys.exit(EXIT_ERROR)
    result = subprocess.run(
        ["git", "diff", "--name-status", "--diff-filter=AMRCD", f"{base}...{head}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(f"ERROR: git diff failed: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(EXIT_ERROR)
    entries: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 2:
            entries.append((parts[0][0], parts[1]))
        elif len(parts) == 3:  # rename/copy: status\tdst\tsrc -> use dst
            entries.append((parts[0][0], parts[2]))
    return entries


def _is_source_change(path: str, source_dirs: list[str]) -> bool:
    if not path.endswith(".py"):
        return False
    if path.endswith("conftest.py") or "/tests/" in path or path == "conftest.py":
        return False
    return any(path.startswith(src_dir + "/") for src_dir in source_dirs)


def _is_fragment(
    path: str, status: str, changelog_dir: str, types: list[str], head: str
) -> bool:
    """True when `path` is a live (never deleted) changelog fragment at HEAD."""
    if status == "D":
        return False
    if not path.startswith(changelog_dir + "/"):
        return False
    name = path.rsplit("/", 1)[-1]
    parts = name.split(".")
    if len(parts) < 3:
        return False
    issue, frag_type, extension = parts[-3], parts[-2], parts[-1]
    if extension != "rst":
        return False
    if not issue.isdigit() or frag_type not in types:
        return False
    exists = subprocess.run(
        ["git", "cat-file", "-e", f"{head}:{path}"],
        capture_output=True,
        check=False,
    )
    return exists.returncode == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0] if __doc__ else "Changelog entry check",
        prog="ci-check-changelog",
    )
    parser.add_argument("--pyproject", default="pyproject.toml")
    parser.add_argument("--source-dir", action="append", default=[])
    parser.add_argument("--changelog-dir", default=None)
    parser.add_argument("base")
    parser.add_argument("head")
    args = parser.parse_args(argv)

    _changed_files(args.base, args.head)

    resolved = _resolve_config(args.pyproject, args.source_dir, args.changelog_dir)
    if resolved is None:
        return EXIT_ERROR
    source_dirs, changelog_dir, types = resolved

    entries = _changed_files(args.base, args.head)

    source_changes = [p for s, p in entries if _is_source_change(p, source_dirs)]
    if not source_changes:
        print("No source changes detected - changelog entry not required.")
        return EXIT_OK

    fragments = [
        p for s, p in entries if _is_fragment(p, s, changelog_dir, types, args.head)
    ]
    if fragments:
        print(f"Changelog entry found: {fragments[0]}")
        return EXIT_OK

    print(
        "ERROR: source files modified without a changelog entry:",
        file=sys.stderr,
    )
    print(file=sys.stderr)
    for path in source_changes:
        print(f"  {path}", file=sys.stderr)
    print(file=sys.stderr)
    print("Fix instructions:", file=sys.stderr)
    print(file=sys.stderr)
    print(
        f"  1. Create a fragment named {changelog_dir}/<issue>.<type>.rst"
        f" where <type> is one of: {', '.join(types)}.",
        file=sys.stderr,
    )
    print(
        f"  2. See {changelog_dir}/README.rst for the expected format.",
        file=sys.stderr,
    )
    print("  3. Commit and push the new fragment.", file=sys.stderr)
    return EXIT_MISSING


if __name__ == "__main__":
    sys.exit(main())
