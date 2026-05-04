"""
Pytest configuration and fixtures for OS-APOW tests.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio

from osapow.models import TaskType, WorkItem, WorkItemStatus
from osapow.queue import GitHubQueue


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_work_item() -> WorkItem:
    """Create a sample work item for testing."""
    return WorkItem(
        id="test-123",
        issue_number=42,
        source_url="https://github.com/test-org/test-repo/issues/42",
        context_body="Test issue body",
        target_repo_slug="test-org/test-repo",
        task_type=TaskType.IMPLEMENT,
        status=WorkItemStatus.QUEUED,
        node_id="test-node-id",
    )


@pytest.fixture
def sample_issue_payload() -> dict:
    """Create a sample GitHub issue webhook payload."""
    return {
        "action": "opened",
        "issue": {
            "id": 123456,
            "number": 42,
            "node_id": "test-node-id",
            "title": "Test Issue",
            "body": "This is a test issue",
            "html_url": "https://github.com/test-org/test-repo/issues/42",
            "labels": [{"name": "bug"}],
        },
        "repository": {
            "id": 789,
            "full_name": "test-org/test-repo",
            "html_url": "https://github.com/test-org/test-repo",
        },
    }


@pytest_asyncio.fixture
async def mock_github_queue() -> AsyncGenerator[GitHubQueue, None]:
    """Create a mock GitHub queue for testing."""
    queue = GitHubQueue(token="test-token", org="test-org", repo="test-repo")
    yield queue
    await queue.close()
