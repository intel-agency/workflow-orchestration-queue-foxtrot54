"""
Tests for OS-APOW Sentinel Orchestrator.
"""

from unittest.mock import AsyncMock, patch

import pytest

from osapow.models import WorkItem
from osapow.sentinel import SentinelOrchestrator


class TestSentinelOrchestrator:
    """Tests for the SentinelOrchestrator."""

    @pytest.fixture
    def sentinel(self) -> SentinelOrchestrator:
        """Create a sentinel orchestrator for testing."""
        return SentinelOrchestrator(
            token="test-token",
            org="test-org",
            repo="test-repo",
            sentinel_id="test-sentinel",
            bot_login="test-bot",
            poll_interval=1,
            heartbeat_interval=60,
        )

    def test_sentinel_initialization(self, sentinel: SentinelOrchestrator) -> None:
        """Test sentinel initialization."""
        assert sentinel.sentinel_id == "test-sentinel"
        assert sentinel.bot_login == "test-bot"
        assert sentinel.poll_interval == 1
        assert sentinel.heartbeat_interval == 60
        assert sentinel._running is False
        assert sentinel._current_task is None

    def test_build_completion_comment_success(
        self, sentinel: SentinelOrchestrator, sample_work_item: WorkItem
    ) -> None:
        """Test building a success completion comment."""
        comment = sentinel._build_completion_comment(sample_work_item, success=True)
        assert "✅" in comment
        assert "completed successfully" in comment
        assert sentinel.sentinel_id in comment

    def test_build_completion_comment_failure(
        self, sentinel: SentinelOrchestrator, sample_work_item: WorkItem
    ) -> None:
        """Test building a failure completion comment."""
        comment = sentinel._build_completion_comment(sample_work_item, success=False)
        assert "❌" in comment
        assert "failed" in comment
        assert sentinel.sentinel_id in comment

    @pytest.mark.asyncio
    async def test_sentinel_graceful_shutdown(self, sentinel: SentinelOrchestrator) -> None:
        """Test that sentinel handles shutdown gracefully."""
        sentinel._running = True
        sentinel._handle_shutdown()
        assert sentinel._running is False

    @pytest.mark.asyncio
    async def test_cleanup_closes_queue(self, sentinel: SentinelOrchestrator) -> None:
        """Test that cleanup closes the queue connection."""
        with patch.object(sentinel.queue, "close", new_callable=AsyncMock) as mock_close:
            await sentinel._cleanup()
            mock_close.assert_called_once()
