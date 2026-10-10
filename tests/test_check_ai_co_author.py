from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from conftest import SCRIPTS_DIR

HOOK = SCRIPTS_DIR / "check-ai-co-author.py"


def run_hook(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOK), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_violating_message_exits_1_with_remediation(tmp_path: Path) -> None:
    msg = tmp_path / "COMMIT_EDITMSG"
    msg.write_text("fix\n\nCo-authored-by: Claude <noreply@anthropic.com>\n")
    result = run_hook(str(msg))
    assert result.returncode == 1
    assert "Co-authored-by: Claude <noreply@anthropic.com>" in result.stderr
    assert "Assisted-by:" in result.stderr


def test_clean_message_exits_0(tmp_path: Path) -> None:
    msg = tmp_path / "COMMIT_EDITMSG"
    msg.write_text("fix\n\nCo-authored-by: Jane Doe <jane@example.org>\n")
    result = run_hook(str(msg))
    assert result.returncode == 0
    assert result.stderr == ""


def test_assisted_by_only_exits_0(tmp_path: Path) -> None:
    msg = tmp_path / "COMMIT_EDITMSG"
    msg.write_text("fix\n\nAssisted-by: Claude:claude-opus\n")
    result = run_hook(str(msg))
    assert result.returncode == 0
    assert result.stderr == ""


def test_missing_path_exits_0(tmp_path: Path) -> None:
    result = run_hook(str(tmp_path / "does-not-exist"))
    assert result.returncode == 0
    assert result.stderr == ""


def test_help_exits_0() -> None:
    result = run_hook("--help")
    assert result.returncode == 0
    assert "commit_msg_file" in result.stdout
