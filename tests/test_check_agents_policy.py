import importlib.util
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check-agents-policy.py"
FIXTURE_POLICY = Path(__file__).resolve().parent / "fixtures" / "AI-POLICY-fixture.md"

_spec = importlib.util.spec_from_file_location("check_agents_policy", SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

BEGIN = mod.BEGIN
END = mod.END
MANUAL = mod.MANUAL
BARE_MANUAL = mod.BARE_MANUAL
MANUAL_LINE = MANUAL + " notes -->"
MANUAL_LINE_2 = MANUAL + " second section -->"


def canonical_inner() -> str:
    text = FIXTURE_POLICY.read_text(encoding="utf-8")
    return text.split(BEGIN, 1)[1].split(END, 1)[0].strip("\n")


def full_block(stale: bool = False) -> str:
    inner = canonical_inner()
    if stale:
        inner = inner.replace("Write tests", "Skip tests")
    return BEGIN + "\n" + inner + "\n" + END


def write_file(path: Path, text: str, nl: str = "\n") -> None:
    path.write_bytes(text.replace("\n", nl).encode("utf-8"))


def run(policy: Path, files, fix: bool = False):
    argv = ["--policy", str(policy)] + [str(f) for f in files]
    if fix:
        argv.append("--fix")
    return mod.main(argv)


def test_script_is_executable():
    assert os.access(SCRIPT, os.X_OK)


def test_help_exit_zero():
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "AI policy" in proc.stdout


def test_identical_block_passes_without_writing(tmp_path):
    target = tmp_path / "AGENTS.md"
    write_file(
        target, "Intro\n\n" + MANUAL_LINE + "\n\n" + full_block() + "\n\nFooter\n"
    )
    before = target.read_bytes()
    before_mtime = target.stat().st_mtime_ns
    assert run(FIXTURE_POLICY, [target]) == 0
    assert target.read_bytes() == before
    assert target.stat().st_mtime_ns == before_mtime


def test_missing_block_no_marker_exit_1_and_no_mutation(tmp_path, capsys):
    target = tmp_path / "AGENTS.md"
    text = "# Guide\n\nBe nice.\n"
    write_file(target, text)
    assert run(FIXTURE_POLICY, [target]) == 1
    captured = capsys.readouterr()
    assert "not pinned" in captured.err
    assert str(target) in captured.err
    assert target.read_bytes() == text.encode()


def test_missing_block_fix_appends_bare_manual_and_block(tmp_path):
    target = tmp_path / "AGENTS.md"
    write_file(target, "# Guide\n\nBe nice.\n")
    assert run(FIXTURE_POLICY, [target], fix=True) == 1
    after = target.read_bytes()
    text = after.decode()
    assert BARE_MANUAL in text
    assert MANUAL_LINE not in text
    assert text.index(BARE_MANUAL) < text.index(BEGIN)
    assert text.endswith(END + "\n")
    assert after.count(BEGIN.encode()) == 1 and after.count(END.encode()) == 1
    assert run(FIXTURE_POLICY, [target]) == 0


def test_missing_block_fix_appends_after_manual_marker(tmp_path):
    target = tmp_path / "AGENTS.md"
    write_file(target, "Title\n\n" + MANUAL_LINE + "\nHandwritten notes.\n")
    assert run(FIXTURE_POLICY, [target], fix=True) == 1
    text = target.read_bytes().decode()
    assert "Handwritten notes." in text
    assert text.endswith(END + "\n")
    assert run(FIXTURE_POLICY, [target]) == 0


def test_two_markers_fix_appends_block_at_end(tmp_path):
    target = tmp_path / "AGENTS.md"
    write_file(
        target,
        "Top text\n" + MANUAL_LINE + "\n"
        "middle text\n" + MANUAL_LINE_2 + "\n"
        "bottom text\n",
    )
    assert run(FIXTURE_POLICY, [target], fix=True) == 1
    new = target.read_bytes().decode()
    assert new.startswith("Top text\n")
    assert new.count(MANUAL) == 2
    assert new.index(MANUAL_LINE) < new.index(MANUAL_LINE_2) < new.index(BEGIN)
    assert "middle text" in new
    assert "bottom text" in new
    assert new.endswith(END + "\n")
    assert run(FIXTURE_POLICY, [target]) == 0


def test_stale_block_exit_1_with_unified_diff(tmp_path, capsys):
    target = tmp_path / "AGENTS.md"
    write_file(
        target, "Intro\n" + MANUAL_LINE + "\n" + full_block(stale=True) + "\nFooter\n"
    )
    before = target.read_bytes()
    assert run(FIXTURE_POLICY, [target]) == 1
    captured = capsys.readouterr()
    assert "--- canonical AI policy block" in captured.out
    assert "+++ " + str(target) in captured.out
    assert "+2. Skip tests before fixing bugs." in captured.out
    assert "-2. Write tests before fixing bugs." in captured.out
    assert target.read_bytes() == before


def test_stale_block_fix_replaces_in_place(tmp_path):
    target = tmp_path / "AGENTS.md"
    write_file(
        target, "Intro\n" + MANUAL_LINE + "\n" + full_block(stale=True) + "\nFooter\n"
    )
    assert run(FIXTURE_POLICY, [target], fix=True) == 1
    text = target.read_bytes().decode()
    assert text.startswith("Intro\n")
    assert text.endswith("\nFooter\n")
    assert "Skip tests" not in text
    assert "Write tests" in text
    assert MANUAL_LINE in text
    assert run(FIXTURE_POLICY, [target]) == 0


def test_crlf_identical_block_compared_clean_and_not_written(tmp_path):
    target = tmp_path / "AGENTS.md"
    write_file(
        target,
        "Intro\n" + MANUAL_LINE + "\n" + full_block() + "\nFooter\n",
        nl="\r\n",
    )
    before = target.read_bytes()
    assert b"\r\n" in before
    assert before.count(b"\n") == before.count(b"\r\n")
    before_mtime = target.stat().st_mtime_ns
    assert run(FIXTURE_POLICY, [target]) == 0
    assert target.stat().st_mtime_ns == before_mtime
    assert target.read_bytes() == before


def test_crlf_stale_block_fix_preserves_crlf_and_outside_bytes(tmp_path):
    target = tmp_path / "AGENTS.md"
    write_file(
        target,
        "Intro\r\n" + MANUAL_LINE + "\r\n" + full_block(stale=True) + "\r\nFooter\r\n",
    )
    before = target.read_bytes()
    assert run(FIXTURE_POLICY, [target], fix=True) == 1
    after = target.read_bytes()
    assert after.count(b"\n") == after.count(b"\r\n")
    assert b"Skip tests" not in after
    assert after.startswith(before[: before.index(BEGIN.encode())])
    assert after.endswith(b"Footer\r\n")
    assert (END.encode() + b"\r\n" + b"Footer\r\n") in after
    assert after.count(MANUAL_LINE.encode()) == 1
    assert run(FIXTURE_POLICY, [target]) == 0


def test_duplicate_sentinel_pairs_exit_2_no_mutation(tmp_path):
    target = tmp_path / "AGENTS.md"
    text = (
        "Intro\n"
        + MANUAL_LINE
        + "\n"
        + full_block()
        + "\n"
        + full_block()
        + "\nFooter\n"
    )
    write_file(target, text)
    for fix in (False, True):
        assert run(FIXTURE_POLICY, [target], fix=fix) == 2
        assert target.read_bytes() == text.encode()


def test_pair_above_manual_marker_exit_2_no_mutation(tmp_path):
    target = tmp_path / "AGENTS.md"
    text = "Intro\n" + full_block() + "\n" + MANUAL_LINE + "\nFooter\n"
    write_file(target, text)
    for fix in (False, True):
        assert run(FIXTURE_POLICY, [target], fix=fix) == 2
        assert target.read_bytes() == text.encode()


def test_end_before_begin_exit_2_no_mutation(tmp_path):
    target = tmp_path / "AGENTS.md"
    text = "Intro\n" + END + "\nmiddle\n" + BEGIN + "\nFooter\n"
    write_file(target, text)
    for fix in (False, True):
        assert run(FIXTURE_POLICY, [target], fix=fix) == 2
        assert target.read_bytes() == text.encode()


def test_single_sentinel_exit_2_no_mutation(tmp_path):
    for text in ("Intro\n" + END + "\nFooter\n", "Intro\n" + BEGIN + "\nFooter\n"):
        target = tmp_path / "AGENTS.md"
        write_file(target, text)
        for fix in (False, True):
            assert run(FIXTURE_POLICY, [target], fix=fix) == 2
            assert target.read_bytes() == text.encode()


def test_missing_target_file_exit_2(tmp_path, capsys):
    missing = tmp_path / "nope.md"
    assert run(FIXTURE_POLICY, [missing]) == 2
    assert str(missing) in capsys.readouterr().err


def test_policy_without_sentinels_exit_2(tmp_path):
    policy = tmp_path / "AI-POLICY.md"
    policy.write_text("# Policy\nplain text only\n", encoding="utf-8")
    target = tmp_path / "AGENTS.md"
    write_file(target, "Intro\n" + MANUAL_LINE + "\n" + full_block() + "\n")
    for fix in (False, True):
        assert run(policy, [target], fix=fix) == 2


def test_multiple_files_report_worst_exit_code(tmp_path):
    ok = tmp_path / "a.md"
    write_file(ok, MANUAL_LINE + "\n" + full_block() + "\n")
    stale = tmp_path / "b.md"
    write_file(stale, MANUAL_LINE + "\n" + full_block(stale=True) + "\n")
    missing = tmp_path / "gone.md"
    assert run(FIXTURE_POLICY, [ok, stale]) == 1
    assert run(FIXTURE_POLICY, [ok, missing]) == 2


def test_fix_on_file_without_trailing_newline(tmp_path):
    target = tmp_path / "AGENTS.md"
    target.write_bytes(b"Notes")
    assert run(FIXTURE_POLICY, [target], fix=True) == 1
    text = target.read_bytes().decode()
    assert text.startswith("Notes")
    assert BARE_MANUAL in text
    assert text.endswith(END + "\n")
    assert run(FIXTURE_POLICY, [target]) == 0
