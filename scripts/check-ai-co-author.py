#!/usr/bin/env python3
"""Commit-msg hook: reject Co-authored-by trailers referencing AI tools.

HyperSpy uses ``Assisted-by:`` for AI attribution.  ``Co-authored-by:`` is
reserved for human co-authors.  Several AI tools (Claude Code, VS Code with
Copilot, Cursor) add ``Co-authored-by:`` to commits by default - this hook
blocks them before the commit is created.

To use this hook, install pre-commit with the ``commit-msg`` stage::

    pre-commit install --hook-type commit-msg

Usage::

    check-ai-co-author.py COMMIT_MSG_FILE
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hyperspy_ai_patterns import find_ai_co_author_lines


def check_commit_message(filepath: str) -> int:
    """Return 0 if OK, 1 if prohibited trailers found."""
    path = Path(filepath)
    if not path.exists():
        # Pre-commit may pass a non-existent path on empty commits
        return 0

    content = path.read_text(encoding="utf-8")
    violations: list[str] = find_ai_co_author_lines(content)

    if violations:
        print(
            "ERROR: Prohibited Co-authored-by trailers found:",
            file=sys.stderr,
        )
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        print(file=sys.stderr)
        print(
            "HyperSpy uses Assisted-by: for AI tool attribution, not Co-authored-by:.",
            file=sys.stderr,
        )
        print(
            "Several AI tools add Co-authored-by: by default "
            "(Claude Code, VS Code Copilot, Cursor).",
            file=sys.stderr,
        )
        print("Please strip it and use instead:", file=sys.stderr)
        print(file=sys.stderr)
        print(
            "  Assisted-by: <tool-name>:<model-version>",
            file=sys.stderr,
        )
        print(
            "  Example: Assisted-by: Claude:claude-sonnet-4-6",
            file=sys.stderr,
        )
        return 1

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reject Co-authored-by trailers that name AI tools.",
    )
    parser.add_argument("commit_msg_file", help="path to the commit message file")
    args = parser.parse_args(argv)
    return check_commit_message(args.commit_msg_file)


if __name__ == "__main__":
    sys.exit(main())
