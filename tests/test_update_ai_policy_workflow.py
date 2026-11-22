from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
COMPLIANCE = REPO_ROOT / ".github" / "workflows" / "compliance.yml"
SCHEDULE = REPO_ROOT / ".github" / "workflows" / "update-ai-policy-schedule.yml"


def test_compliance_workflow_supports_policy_updates() -> None:
    text = COMPLIANCE.read_text(encoding="utf-8")

    assert "workflow_call:" in text
    assert "update_policy:" in text
    assert "default: false" in text
    assert "ai-policy-update:" in text
    assert "peter-evans/create-pull-request@v8" in text
    assert "draft: false" in text
    assert "branch: ${{ inputs.policy_branch }}" in text
    assert "if: ${{ !inputs.update_policy }}" in text
    assert "if: ${{ !inputs.update_policy && inputs.check_changelog }}" in text
    assert "if: ${{ !inputs.update_policy && inputs.check_agents_policy }}" in text
    assert not (COMPLIANCE.parent / "update-ai-policy.yml").exists()


def test_policy_update_schedule_calls_compliance() -> None:
    text = SCHEDULE.read_text(encoding="utf-8")

    assert 'cron: "17 3 * * *"' in text
    assert "uses: hyperspy/.github/.github/workflows/compliance.yml@" in text
    assert "update_policy: true" in text
