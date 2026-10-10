#!/usr/bin/env python3
"""Check that AGENTS.md files pin the canonical HyperSpy AI policy block.

Reads the canonical block (between the BEGIN and END sentinels) from
AI-POLICY.md, then verifies each target AGENTS.md pins the same block:

- Missing policy block or missing/malformed target layout -> exit 2.
- Target block differs (whitespace-insensitive) -> exit 1 with a unified diff;
  with --fix, splice in the canonical block (byte-preserving) and exit 1.
- Target block matches -> exit 0.

Newline style (CRLF vs LF) and every byte outside the block span are
preserved when fixing. Sentinels only count as standalone lines.
"""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

BEGIN = "<!-- hyperspy-ai-policy:begin -->"
END = "<!-- hyperspy-ai-policy:end -->"
MANUAL = "<!-- MANUAL:"
BARE_MANUAL = (
    "<!-- MANUAL: Any manually added notes below this line"
    " are preserved on regeneration -->"
)

MSG_UPDATED = (
    "Updated {path}: HyperSpy AI policy block inserted/refreshed"
    " - stage it and commit again"
)
MSG_RERUN = (
    "run: pre-commit run check-agents-policy --all-files"
    "  (or python3 check-agents-policy.py --fix {path})"
)

EXIT_OK = 0
EXIT_DIFF = 1
EXIT_ERROR = 2


def _standalone(line: bytes, sentinel: str) -> bool:
    return line.strip() == sentinel.encode()


def _extract_policy_block(path: Path) -> bytes | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    lines = data.split(b"\n")
    try:
        begin = next(i for i, line in enumerate(lines) if _standalone(line, BEGIN))
        end = next(
            i
            for i, line in enumerate(lines[begin + 1 :], start=begin + 1)
            if _standalone(line, END)
        )
    except StopIteration:
        return None
    return b"\n".join(lines[begin : end + 1])


def _normalise(block: bytes) -> list[str]:
    lines = [line.decode("utf-8", "replace").rstrip() for line in block.split(b"\n")]
    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def _block_span(data: bytes) -> tuple[int, int] | None:
    # Byte span [start, end) covering the BEGIN line through the END line's
    # trailing newline; end may be len(data)+1 when the file ends right after
    # the END line without a final newline (bytes slicing clamps safely).
    lines = data.split(b"\n")
    begins = [i for i, line in enumerate(lines) if _standalone(line, BEGIN)]
    ends = [i for i, line in enumerate(lines) if _standalone(line, END)]
    if len(begins) != 1 or len(ends) != 1:
        return None
    begin_i, end_i = begins[0], ends[0]
    if end_i <= begin_i:
        return None
    start = sum(len(line) + 1 for line in lines[:begin_i])
    end = sum(len(line) + 1 for line in lines[: end_i + 1])
    return start, end


def _first_manual_index(data: bytes) -> int | None:
    for i, line in enumerate(data.split(b"\n")):
        s = line.decode("utf-8", "replace").strip()
        if s.startswith(MANUAL) and s.endswith("-->"):
            return i
    return None


def _newline_style(data: bytes) -> bytes:
    return b"\r\n" if b"\r\n" in data else b"\n"


def _fix_target(path: Path, block: bytes) -> None:
    data = path.read_bytes()
    nl = _newline_style(data)
    block_lf = block.replace(b"\r\n", b"\n").replace(b"\r", b"\n").rstrip(b"\n")
    block_joined = block_lf.replace(b"\n", nl) + nl
    span = _block_span(data)
    if span is not None:
        start, end = span
        data = data[:start] + block_joined + data[end:]
    else:
        if not data.endswith(b"\n"):
            data += nl
        if _first_manual_index(data) is None:
            data += (BARE_MANUAL + "\n\n").encode() + block_joined
        else:
            data += block_joined
    path.write_bytes(data)


def _check_target(path: Path, block: bytes, fix: bool) -> int:
    if not path.exists():
        print(f"ERROR: {path} not found", file=sys.stderr)
        return EXIT_ERROR
    data = path.read_bytes()
    lines = data.split(b"\n")
    begins = [i for i, line in enumerate(lines) if _standalone(line, BEGIN)]
    ends = [i for i, line in enumerate(lines) if _standalone(line, END)]
    manual_i = _first_manual_index(data)
    canonical = _normalise(block)

    if len(begins) == 1 and len(ends) == 1:
        begin_i, end_i = begins[0], ends[0]
        if end_i <= begin_i:
            print(
                f"ERROR: {path}: malformed policy block"
                " (end sentinel before begin sentinel)",
                file=sys.stderr,
            )
            return EXIT_ERROR
        if manual_i is not None and begin_i < manual_i:
            print(
                f"ERROR: {path}: policy block sits above the MANUAL marker",
                file=sys.stderr,
            )
            return EXIT_ERROR
        target = _normalise(b"\n".join(lines[begin_i : end_i + 1]))
        if target == canonical:
            return EXIT_OK
        if not fix:
            diff = difflib.unified_diff(
                canonical,
                target,
                fromfile="canonical AI policy block",
                tofile=str(path),
                lineterm="",
            )
            sys.stdout.write("\n".join(diff) + "\n")
            print(MSG_RERUN.format(path=path))
            return EXIT_DIFF
        _fix_target(path, block)
        print(MSG_UPDATED.format(path=path))
        return EXIT_DIFF

    if begins or ends:
        print(
            f"ERROR: {path}: malformed policy block"
            " (sentinels must appear exactly once each)",
            file=sys.stderr,
        )
        return EXIT_ERROR

    if fix:
        _fix_target(path, block)
        print(MSG_UPDATED.format(path=path))
        return EXIT_DIFF
    if manual_i is not None:
        print(
            f"ERROR: {path}: HyperSpy AI policy block not pinned after the"
            " MANUAL marker",
            file=sys.stderr,
        )
    else:
        print(
            f"ERROR: {path}: HyperSpy AI policy block not pinned and no"
            " MANUAL marker found",
            file=sys.stderr,
        )
    return EXIT_DIFF


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0] if __doc__ else "Check AI policy pins",
        prog="check-agents-policy",
    )
    parser.add_argument(
        "files",
        nargs="*",
        default=["AGENTS.md"],
        help="AGENTS.md files to check (default: AGENTS.md)",
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "AI-POLICY.md",
        help="path to AI-POLICY.md (default: <repo root>/AI-POLICY.md)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="insert or refresh the policy block in each target file",
    )
    args = parser.parse_args(argv)

    block = _extract_policy_block(args.policy)
    if block is None:
        print(
            f"ERROR: {args.policy}: no policy block found (expected {BEGIN} .. {END})",
            file=sys.stderr,
        )
        return EXIT_ERROR

    worst = EXIT_OK
    for path in (Path(f) for f in args.files):
        worst = max(worst, _check_target(path, block, args.fix))
    return worst


if __name__ == "__main__":
    sys.exit(main())
