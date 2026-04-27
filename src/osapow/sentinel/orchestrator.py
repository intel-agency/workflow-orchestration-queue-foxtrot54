"""
OS-APOW Sentinel Orchestrator

Persistent supervisor managing worker lifecycles. The "Brain" of the
4-Pillar Architecture that coordinates task discovery, claiming, and
dispatch to the opencode worker environment.

See: OS-APOW Architecture Guide v3.2
"""

import asyncio
import contextlib
import logging
import os
import random
import signal
import sys
import uuid
from datetime import UTC, datetime

import httpx

from osapow.models import WorkItem, WorkItemStatus
from osapow.queue import GitHubQueue

logger = logging.getLogger("OS-APOW")


class SentinelOrchestrator:
    """Persistent supervisor managing worker lifecycles.

    Lifecycle Management:
    1. POLLING DISCOVERY (every 60s)
    2. AUTH SYNCHRONIZATION
    3. SHELL-BRIDGE PROTOCOL
    4. TELEMETRY (Heartbeat comments)
    5. ENVIRONMENT RESET
    """

    def __init__(
        self,
        token: str,
        org: str,
        repo: str,
        sentinel_id: str = "sentinel-01",
        bot_login: str = "",
        poll_interval: int = 60,
        heartbeat_interval: int = 300,
    ):
        self.queue = GitHubQueue(token=token, org=org, repo=repo)
        self.sentinel_id = sentinel_id
        self.bot_login = bot_login
        self.poll_interval = poll_interval
        self.heartbeat_interval = heartbeat_interval
        self._running = False
        self._current_task: WorkItem | None = None
        self._shutdown_event = asyncio.Event()
        self._running_heartbeat: asyncio.Task[None] | None = None
        self._rate_limit_backoff: float = 0.0

    async def start(self) -> None:
        """Start the sentinel polling loop."""
        self._running = True
        logger.info(
            f"Sentinel {self.sentinel_id} starting - "
            f"polling {self.queue.org}/{self.queue.repo} every {self.poll_interval}s"
        )

        # Set up signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._handle_shutdown)

        try:
            await self._run_loop()
        finally:
            await self._cleanup()

    def _handle_shutdown(self) -> None:
        """Handle shutdown signals gracefully."""
        logger.info(f"Sentinel {self.sentinel_id} received shutdown signal")
        self._running = False
        self._shutdown_event.set()

    async def _run_loop(self) -> None:
        """Main polling loop with rate-limit backoff."""
        while self._running:
            # Apply any pending backoff from rate limiting
            if self._rate_limit_backoff > 0:
                logger.warning(f"Rate limited - backing off for {self._rate_limit_backoff:.1f}s")
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(), timeout=self._rate_limit_backoff
                    )
                    break  # Shutdown during backoff
                except TimeoutError:
                    pass  # Backoff complete

            try:
                await self._poll_and_process()
                # Reset backoff on successful poll
                self._rate_limit_backoff = 0.0
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (403, 429):
                    # Exponential backoff with jitter for rate limits
                    base_backoff = min(self._rate_limit_backoff * 2 + 1, 300)  # Cap at 5 min
                    jitter = random.uniform(0, base_backoff * 0.1)  # 10% jitter
                    self._rate_limit_backoff = base_backoff + jitter
                    logger.warning(
                        f"GitHub API rate limit (HTTP {e.response.status_code}), "
                        f"next backoff: {self._rate_limit_backoff:.1f}s"
                    )
                else:
                    logger.error(f"HTTP error in polling loop: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Error in polling loop: {e}", exc_info=True)

            # Wait for next poll or shutdown
            try:
                await asyncio.wait_for(self._shutdown_event.wait(), timeout=self.poll_interval)
                break  # Shutdown event was set
            except TimeoutError:
                pass  # Normal poll interval

    async def _poll_and_process(self) -> None:
        """Poll for queued tasks and process them."""
        tasks = await self.queue.fetch_queued_tasks()
        if not tasks:
            logger.debug("No queued tasks found")
            return

        logger.info(f"Found {len(tasks)} queued task(s)")

        for task in tasks:
            if not self._running:
                break

            if await self._claim_and_execute(task):
                break  # Only process one task at a time

    async def _claim_and_execute(self, task: WorkItem) -> bool:
        """Attempt to claim and execute a task.

        Returns True if task was successfully claimed and executed.
        """
        logger.info(f"Attempting to claim task #{task.issue_number}")

        if not await self.queue.claim_task(task, self.sentinel_id, self.bot_login):
            logger.warning(f"Failed to claim task #{task.issue_number}")
            return False

        self._current_task = task
        start_time = datetime.now(UTC)

        # Start heartbeat background task
        self._running_heartbeat = asyncio.create_task(self._heartbeat_loop(task, start_time))

        try:
            success = await self._execute_task(task)
            final_status = WorkItemStatus.SUCCESS if success else WorkItemStatus.ERROR
            await self.queue.update_status(
                task,
                final_status,
                comment=self._build_completion_comment(task, success),
            )
            logger.info(f"Task #{task.issue_number} completed with status: {final_status}")
        except Exception as e:
            logger.error(f"Task #{task.issue_number} failed: {e}", exc_info=True)
            await self.queue.update_status(
                task, WorkItemStatus.ERROR, comment=f"❌ **Error:** {str(e)[:500]}"
            )
        finally:
            # Cancel heartbeat task
            if self._running_heartbeat:
                self._running_heartbeat.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._running_heartbeat
                self._running_heartbeat = None
            self._current_task = None

        return True

    async def _heartbeat_loop(self, task: WorkItem, start_time: datetime) -> None:
        """Background task that posts heartbeat comments during execution."""
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                elapsed = int((datetime.now(UTC) - start_time).total_seconds())
                await self.queue.post_heartbeat(task, self.sentinel_id, elapsed)
        except asyncio.CancelledError:
            logger.debug(f"Heartbeat loop cancelled for task #{task.issue_number}")
            raise

    async def _execute_task(self, task: WorkItem) -> bool:
        """Execute a claimed task.

        TODO: Implement shell-bridge protocol to invoke devcontainer-opencode.sh
        """
        logger.info(f"Executing task #{task.issue_number}: {task.task_type.value}")
        # Placeholder - actual implementation will invoke the worker
        logger.warning(
            f"PLACEHOLDER: Task #{task.issue_number} execution is not implemented. "
            "This is a stub that returns success without running any worker command."
        )
        await asyncio.sleep(5)  # Simulate work
        return True

    def _build_completion_comment(self, task: WorkItem, success: bool) -> str:
        """Build a completion comment for the task."""
        emoji = "✅" if success else "❌"
        status = "completed successfully" if success else "failed"
        return (
            f"{emoji} **Task {status}**\n"
            f"- **Sentinel:** {self.sentinel_id}\n"
            f"- **Completed:** {datetime.now(UTC).isoformat()}\n"
            f"- **Task Type:** {task.task_type.value}"
        )

    async def _cleanup(self) -> None:
        """Clean up resources on shutdown."""
        logger.info(f"Sentinel {self.sentinel_id} shutting down...")
        if self._current_task:
            logger.warning(f"Task #{self._current_task.issue_number} interrupted - requeuing")
            try:
                # Requeue the interrupted task by changing label back to queued
                await self.queue.update_status(
                    self._current_task,
                    WorkItemStatus.QUEUED,
                    comment=f"⚠️ **Task Requeued**\n- **Reason:** Sentinel {self.sentinel_id} shutdown",
                )
            except Exception as e:
                logger.error(f"Failed to requeue task #{self._current_task.issue_number}: {e}")
        await self.queue.close()
        logger.info("Cleanup complete")


async def main() -> None:
    """Entry point for running the sentinel."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    token = os.environ.get("GITHUB_TOKEN", "")
    org = os.environ.get("GITHUB_ORG", "")
    repo = os.environ.get("GITHUB_REPO", "")
    bot_login = os.environ.get("SENTINEL_BOT_LOGIN", "")
    poll_interval = int(os.environ.get("SENTINEL_POLL_INTERVAL", "60"))
    heartbeat_interval = int(os.environ.get("HEARTBEAT_INTERVAL", "300"))

    if not all([token, org, repo]):
        logger.error(
            "Missing required environment variables: GITHUB_TOKEN, GITHUB_ORG, GITHUB_REPO"
        )
        sys.exit(1)

    # Generate unique sentinel ID for distributed locking
    sentinel_id = f"sentinel-{uuid.uuid4().hex[:8]}"

    sentinel = SentinelOrchestrator(
        token=token,
        org=org,
        repo=repo,
        sentinel_id=sentinel_id,
        bot_login=bot_login,
        poll_interval=poll_interval,
        heartbeat_interval=heartbeat_interval,
    )

    await sentinel.start()


def run_main() -> None:
    """Synchronous entry point for console script."""
    asyncio.run(main())


if __name__ == "__main__":
    run_main()
