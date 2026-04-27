"""
Tests for OS-APOW Work Item model.
"""

from osapow.models import TaskType, WorkItem, WorkItemStatus, scrub_secrets


class TestWorkItem:
    """Tests for the WorkItem model."""

    def test_create_work_item(self) -> None:
        """Test creating a basic work item."""
        item = WorkItem(
            id="test-123",
            issue_number=1,
            source_url="https://github.com/org/repo/issues/1",
            context_body="Test body",
            target_repo_slug="org/repo",
            task_type=TaskType.IMPLEMENT,
            status=WorkItemStatus.QUEUED,
            node_id="node-123",
        )

        assert item.id == "test-123"
        assert item.issue_number == 1
        assert item.task_type == TaskType.IMPLEMENT
        assert item.status == WorkItemStatus.QUEUED

    def test_task_types(self) -> None:
        """Test all task type values."""
        assert TaskType.PLAN.value == "PLAN"
        assert TaskType.IMPLEMENT.value == "IMPLEMENT"
        assert TaskType.BUGFIX.value == "BUGFIX"

    def test_work_item_statuses(self) -> None:
        """Test all status values."""
        assert WorkItemStatus.QUEUED.value == "agent:queued"
        assert WorkItemStatus.IN_PROGRESS.value == "agent:in-progress"
        assert WorkItemStatus.RECONCILING.value == "agent:reconciling"
        assert WorkItemStatus.SUCCESS.value == "agent:success"
        assert WorkItemStatus.ERROR.value == "agent:error"
        assert WorkItemStatus.INFRA_FAILURE.value == "agent:infra-failure"
        assert WorkItemStatus.STALLED_BUDGET.value == "agent:stalled-budget"


class TestScrubSecrets:
    """Tests for the secret scrubbing function."""

    def test_scrub_github_pat(self) -> None:
        """Test scrubbing GitHub PAT tokens."""
        text = "Token: ghp_1234567890abcdefghijklmnopqrstuvwxyz123456"
        result = scrub_secrets(text)
        assert "ghp_" not in result
        assert "***REDACTED***" in result

    def test_scrub_github_app_token(self) -> None:
        """Test scrubbing GitHub App installation tokens."""
        text = "Token: ghs_1234567890abcdefghijklmnopqrstuvwxyz123456"
        result = scrub_secrets(text)
        assert "ghs_" not in result
        assert "***REDACTED***" in result

    def test_scrub_bearer_token(self) -> None:
        """Test scrubbing Bearer tokens."""
        text = "Authorization: Bearer abc123xyz789=="
        result = scrub_secrets(text)
        assert "Bearer" not in result or "***REDACTED***" in result

    def test_scrub_openai_key(self) -> None:
        """Test scrubbing OpenAI-style API keys."""
        text = "API Key: sk-1234567890abcdefghijklmnop"
        result = scrub_secrets(text)
        assert "sk-" not in result
        assert "***REDACTED***" in result

    def test_scrub_no_secrets(self) -> None:
        """Test that normal text is unchanged."""
        text = "This is normal text with no secrets."
        result = scrub_secrets(text)
        assert result == text

    def test_scrub_custom_replacement(self) -> None:
        """Test using a custom replacement string."""
        text = "Token: ghp_1234567890abcdefghijklmnopqrstuvwxyz123456"
        result = scrub_secrets(text, replacement="[HIDDEN]")
        assert "[HIDDEN]" in result
