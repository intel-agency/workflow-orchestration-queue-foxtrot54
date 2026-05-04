"""
Tests for OS-APOW Notifier Service.
"""

import hashlib
import hmac
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from osapow.models import TaskType
from osapow.notifier.service import WebhookNotifier, create_app
from osapow.queue import GitHubQueue


class TestWebhookNotifier:
    """Tests for the WebhookNotifier class."""

    @pytest.fixture
    def queue(self) -> GitHubQueue:
        """Create a GitHubQueue for testing."""
        return GitHubQueue(token="test-token", org="test-org", repo="test-repo")

    @pytest.fixture
    def notifier(self, queue: GitHubQueue) -> WebhookNotifier:
        """Create a WebhookNotifier with a test secret."""
        return WebhookNotifier(queue=queue, webhook_secret="test-secret")

    def test_verify_signature_valid(self, notifier: WebhookNotifier) -> None:
        """Test that valid HMAC signatures pass verification."""
        payload = b'{"action": "opened"}'
        expected_sig = (
            "sha256="
            + hmac.new(
                b"test-secret",
                payload,
                hashlib.sha256,
            ).hexdigest()
        )
        assert notifier.verify_signature(payload, expected_sig) is True

    def test_verify_signature_invalid(self, notifier: WebhookNotifier) -> None:
        """Test that invalid HMAC signatures fail verification."""
        payload = b'{"action": "opened"}'
        assert notifier.verify_signature(payload, "sha256=invalid") is False

    def test_verify_signature_no_secret_configured(self, queue: GitHubQueue) -> None:
        """Test that missing webhook_secret raises ValueError."""
        notifier_no_secret = WebhookNotifier(queue=queue, webhook_secret="")
        with pytest.raises(ValueError, match="WEBHOOK_SECRET"):
            notifier_no_secret.verify_signature(b"payload", "sha256=abc")

    def test_parse_work_item_issue_opened(self, notifier: WebhookNotifier) -> None:
        """Test parsing a standard issue opened payload with agent:queued label."""
        payload = {
            "action": "opened",
            "issue": {
                "id": 123456,
                "number": 42,
                "node_id": "test-node-id",
                "title": "Test Issue",
                "body": "This is a test issue",
                "html_url": "https://github.com/test-org/test-repo/issues/42",
                "labels": [{"name": "agent:queued"}, {"name": "bug"}],
            },
            "repository": {
                "id": 789,
                "full_name": "test-org/test-repo",
                "html_url": "https://github.com/test-org/test-repo",
            },
        }
        result = notifier.parse_work_item(payload, event_type="issues")
        assert result is not None
        assert result.issue_number == 42
        assert result.target_repo_slug == "test-org/test-repo"
        assert result.task_type == TaskType.BUGFIX

    def test_parse_work_item_with_plan_label(self, notifier: WebhookNotifier) -> None:
        """Test that agent:plan label triggers PLAN task type."""
        payload = {
            "action": "opened",
            "issue": {
                "id": 123,
                "number": 1,
                "node_id": "node-1",
                "title": "My Plan",
                "body": "Plan body",
                "html_url": "https://github.com/org/repo/issues/1",
                "labels": [{"name": "agent:plan"}],
            },
            "repository": {
                "full_name": "org/repo",
            },
        }
        result = notifier.parse_work_item(payload, event_type="issues")
        assert result is not None
        assert result.task_type == TaskType.PLAN

    def test_parse_work_item_with_bug_label(self, notifier: WebhookNotifier) -> None:
        """Test that bug label triggers BUGFIX task type."""
        payload = {
            "action": "opened",
            "issue": {
                "id": 123,
                "number": 1,
                "node_id": "node-1",
                "title": "Bug fix",
                "body": "Bug body",
                "html_url": "https://github.com/org/repo/issues/1",
                "labels": [{"name": "agent:queued"}, {"name": "bug"}],
            },
            "repository": {
                "full_name": "org/repo",
            },
        }
        result = notifier.parse_work_item(payload, event_type="issues")
        assert result is not None
        assert result.task_type == TaskType.BUGFIX

    def test_parse_work_item_no_agent_labels(self, notifier: WebhookNotifier) -> None:
        """Test that issues without OS-APOW labels return None."""
        payload = {
            "action": "opened",
            "issue": {
                "id": 123,
                "number": 1,
                "node_id": "node-1",
                "title": "Regular issue",
                "body": "Body",
                "html_url": "https://github.com/org/repo/issues/1",
                "labels": [{"name": "enhancement"}],
            },
            "repository": {
                "full_name": "org/repo",
            },
        }
        result = notifier.parse_work_item(payload, event_type="issues")
        assert result is None

    def test_parse_work_item_pr_issue_comment_skipped(self, notifier: WebhookNotifier) -> None:
        """Test that PR issue_comment events are skipped."""
        payload = {
            "action": "created",
            "issue": {
                "id": 123,
                "number": 1,
                "node_id": "node-1",
                "title": "PR Title",
                "body": "PR body",
                "html_url": "https://github.com/org/repo/pull/1",
                "labels": [{"name": "agent:queued"}],
                "pull_request": {"url": "https://api.github.com/repos/org/repo/pulls/1"},
            },
            "comment": {"body": "Test comment"},
            "repository": {
                "full_name": "org/repo",
            },
        }
        result = notifier.parse_work_item(payload, event_type="issue_comment")
        assert result is None

    def test_parse_work_item_no_issue(self, notifier: WebhookNotifier) -> None:
        """Test that payloads without issue/PR return None."""
        payload = {"action": "some_action"}
        result = notifier.parse_work_item(payload, event_type="push")
        assert result is None

    def test_parse_work_item_comment_includes_context(self, notifier: WebhookNotifier) -> None:
        """Test that comment body is included in context for issue comments."""
        payload = {
            "action": "created",
            "issue": {
                "id": 123,
                "number": 1,
                "node_id": "node-1",
                "title": "Issue Title",
                "body": "Issue body",
                "html_url": "https://github.com/org/repo/issues/1",
                "labels": [{"name": "agent:in-progress"}],
            },
            "comment": {"body": "This is my review comment"},
            "repository": {
                "full_name": "org/repo",
            },
        }
        result = notifier.parse_work_item(payload, event_type="issue_comment")
        assert result is not None
        assert "This is my review comment" in result.context_body
        assert "Issue body" in result.context_body


class TestNotifierApp:
    """Tests for the FastAPI application endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        """Create a test client with mocked environment."""
        with patch.dict(
            "os.environ",
            {
                "GITHUB_TOKEN": "test-token",
                "WEBHOOK_SECRET": "test-secret",
            },
        ):
            app = create_app()
            return TestClient(app)

    def test_health_check(self, client: TestClient) -> None:
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "osapow-notifier"

    def test_webhook_missing_signature(self, client: TestClient) -> None:
        """Test that webhooks without signature are rejected."""
        response = client.post("/webhook/github", json={"action": "opened"})
        assert response.status_code in (401, 500)

    def test_webhook_ignores_unknown_events(self, client: TestClient) -> None:
        """Test that unknown event types are ignored."""
        payload = b'{"action": "opened"}'
        sig = "sha256=" + hmac.new(b"test-secret", payload, hashlib.sha256).hexdigest()
        response = client.post(
            "/webhook/github",
            content=payload,
            headers={
                "X-Hub-Signature-256": sig,
                "X-GitHub-Event": "push",
                "Content-Type": "application/json",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ignored"
