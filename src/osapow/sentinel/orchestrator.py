"""
OS-APOW Sentinel Orchestrator

Persistent supervisor managing worker lifecycles. The "Brain" of the
4-Pillar Architecture that coordinates task discovery, claiming, and
dispatch to the opencode worker environment.

See: OS-APOW Architecture Guide v3.2
"""

import asyncio
import logging
import os
import signal
from datetime import UTC, datetime

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

    async def start(self):
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

    def _handle_shutdown(self):
        """Handle shutdown signals gracefully."""
        logger.info(f"Sentinel {self.sentinel_id} received shutdown signal")
        self._running = False
        self._shutdown_event.set()

    async def _run_loop(self):
        """Main polling loop."""
        while self._running:
            try:
                await self._poll_and_process()
            except Exception as e:
                logger.error(f"Error in polling loop: {e}", exc_info=True)

            # Wait for next poll or shutdown
            try:
                await asyncio.wait_for(self._shutdown_event.wait(), timeout=self.poll_interval)
                break  # Shutdown event was set
            except TimeoutError:
                pass  # Normal poll interval

    async def _poll_and_process(self):
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
            self._current_task = None

        return True

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

    async def _cleanup(self):
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


async def main():
    """Entry point for running the sentinel."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    token = os.environ.get("GITHUB_TOKEN", "")
    org = os.environ.get("GITHUB_ORG", "")
    repo = os.environ.get("GITHUB_REPO", "")
    bot_login = os.environ.get("SENTINEL_BOT_LOGIN", "")

    if not all([token, org, repo]):
        logger.error(
            "Missing required environment variables: GITHUB_TOKEN, GITHUB_ORG, GITHUB_REPO"
        )
        return

    sentinel = SentinelOrchestrator(
        token=token,
        org=org,
        repo=repo,
        bot_login=bot_login,
    )

    await sentinel.start()


def run_main():
    """Synchronous entry point for console script."""
    asyncio.run(main())


if __name__ == "__main__":
    run_main()
