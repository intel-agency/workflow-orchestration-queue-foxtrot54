"""
Tests for OS-APOW GitHub Queue.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio

from osapow.models import TaskType
from osapow.queue import GitHubQueue, ITaskQueue


class TestGitHubQueue:
    """Tests for the GitHubQueue implementation."""

    @pytest_asyncio.fixture
    async def queue(self) -> GitHubQueue:
        """Create a GitHub queue for testing."""
        q = GitHubQueue(token="test-token", org="test-org", repo="test-repo")
        yield q
        await q.close()

    def test_queue_implements_interface(self, queue: GitHubQueue) -> None:
        """Test that GitHubQueue implements ITaskQueue."""
        assert isinstance(queue, ITaskQueue)

    def test_repo_api_url(self, queue: GitHubQueue) -> None:
        """Test API URL generation."""
        url = queue._repo_api_url("owner/repo")
        assert url == "https://api.github.com/repos/owner/repo"

    @pytest.mark.asyncio
    async def test_fetch_queued_tasks_no_org_repo(self) -> None:
        """Test that fetch requires org and repo."""
        queue = GitHubQueue(token="test-token")
        tasks = await queue.fetch_queued_tasks()
        assert tasks == []
        await queue.close()

    @pytest.mark.asyncio
    async def test_fetch_queued_tasks_empty_response(self, queue: GitHubQueue) -> None:
        """Test fetching tasks with empty response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        with patch.object(queue._client, "get", new_callable=AsyncMock, return_value=mock_response):
            tasks = await queue.fetch_queued_tasks()
            assert tasks == []

    @pytest.mark.asyncio
    async def test_fetch_queued_tasks_with_issues(self, queue: GitHubQueue) -> None:
        """Test fetching tasks with issues."""
        mock_issues = [
            {
                "id": 123,
                "number": 1,
                "node_id": "node-1",
                "title": "Test Issue",
                "body": "Test body",
                "html_url": "https://github.com/test-org/test-repo/issues/1",
                "labels": [{"name": "agent:queued"}],
            }
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_issues

        with patch.object(queue._client, "get", new_callable=AsyncMock, return_value=mock_response):
            tasks = await queue.fetch_queued_tasks()
            assert len(tasks) == 1
            assert tasks[0].issue_number == 1
            assert tasks[0].task_type == TaskType.IMPLEMENT

    @pytest.mark.asyncio
    async def test_fetch_queued_tasks_plan_type(self, queue: GitHubQueue) -> None:
        """Test that plan issues are detected correctly."""
        mock_issues = [
            {
                "id": 123,
                "number": 1,
                "node_id": "node-1",
                "title": "[Plan] Create feature",
                "body": "Plan body",
                "html_url": "https://github.com/test-org/test-repo/issues/1",
                "labels": [{"name": "agent:queued"}],
            }
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_issues

        with patch.object(queue._client, "get", new_callable=AsyncMock, return_value=mock_response):
            tasks = await queue.fetch_queued_tasks()
            assert len(tasks) == 1
            assert tasks[0].task_type == TaskType.PLAN

    @pytest.mark.asyncio
    async def test_fetch_queued_tasks_bugfix_type(self, queue: GitHubQueue) -> None:
        """Test that bug issues are detected correctly."""
        mock_issues = [
            {
                "id": 123,
                "number": 1,
                "node_id": "node-1",
                "title": "Fix this bug",
                "body": "Bug body",
                "html_url": "https://github.com/test-org/test-repo/issues/1",
                "labels": [{"name": "agent:queued"}, {"name": "bug"}],
            }
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_issues

        with patch.object(queue._client, "get", new_callable=AsyncMock, return_value=mock_response):
            tasks = await queue.fetch_queued_tasks()
            assert len(tasks) == 1
            assert tasks[0].task_type == TaskType.BUGFIX
