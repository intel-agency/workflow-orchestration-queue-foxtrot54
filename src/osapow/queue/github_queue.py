"""
OS-APOW GitHub Queue

Consolidated GitHub-backed work queue used by both the Sentinel
Orchestrator and the Work Event Notifier. Implements the ITaskQueue
ABC so the provider can be swapped to Linear, Jira, etc. in the future.

See: OS-APOW Simplification Report, S-1 / S-6
"""

import logging
import re
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

import httpx

from osapow.models.work_item import (
    TaskType,
    WorkItem,
    WorkItemStatus,
    scrub_secrets,
)

logger = logging.getLogger("OS-APOW")


# --- Abstract Interface (kept per S-1 for future provider swapping) ---


class ITaskQueue(ABC):
    """Interface for the Work Queue (e.g., GH Issues, Linear, Jira, etc.)"""

    @abstractmethod
    async def add_to_queue(self, item: WorkItem) -> bool:
        pass

    @abstractmethod
    async def fetch_queued_tasks(self) -> list[WorkItem]:
        pass

    @abstractmethod
    async def update_status(
        self, item: WorkItem, status: WorkItemStatus, comment: str | None = None
    ) -> None:
        pass


# --- Concrete Implementation: GitHub Issues ---


# Default timeout for stale claim detection (in seconds)
DEFAULT_CLAIM_STALE_TIMEOUT_SECS = 1800  # 30 minutes


class GitHubQueue(ITaskQueue):
    """GitHub-backed work queue with connection pooling.

    Used by both the Sentinel Orchestrator and the Work Event Notifier.
    The sentinel passes org/repo for polling; the notifier only needs a
    token since it derives the repo from the webhook payload.
    """

    def __init__(
        self,
        token: str,
        org: str = "",
        repo: str = "",
        claim_stale_timeout_secs: int = DEFAULT_CLAIM_STALE_TIMEOUT_SECS,
    ):
        self.token = token
        self.org = org
        self.repo = repo
        self.claim_stale_timeout_secs = claim_stale_timeout_secs
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        self._client = httpx.AsyncClient(
            headers=self.headers,
            timeout=30.0,
        )

    async def close(self) -> None:
        """Release the connection pool. Call during graceful shutdown."""
        await self._client.aclose()

    def _repo_api_url(self, repo_slug: str) -> str:
        return f"https://api.github.com/repos/{repo_slug}"

    # --- ITaskQueue implementation ---

    async def add_to_queue(self, item: WorkItem) -> bool:
        """Add the agent:queued label to a GitHub issue."""
        url = f"{self._repo_api_url(item.target_repo_slug)}/issues/{item.issue_number}/labels"
        resp = await self._client.post(url, json={"labels": [WorkItemStatus.QUEUED.value]})
        if resp.status_code in (200, 201):
            logger.info(f"Queued issue #{item.issue_number} ({item.task_type.value})")
            return True
        logger.error(f"Failed to queue #{item.issue_number}: {resp.status_code}")
        return False

    async def fetch_queued_tasks(self) -> list[WorkItem]:
        """Query GitHub for issues labeled 'agent:queued' in the configured repo.

        Note: Cross-repo org-wide polling via the Search API is planned
        for a future phase. Currently requires org and repo to be set.
        """
        if not self.org or not self.repo:
            logger.warning("fetch_queued_tasks requires org and repo to be set")
            return []

        url = f"{self._repo_api_url(f'{self.org}/{self.repo}')}/issues"
        params: dict[str, str | int] = {
            "labels": WorkItemStatus.QUEUED.value,
            "state": "open",
            "per_page": 100,
        }

        all_issues: list[dict[str, Any]] = []
        page = 1

        while True:
            params["page"] = page
            response = await self._client.get(url, params=params)

            if response.status_code in (403, 429):
                # Propagate rate-limit errors so the sentinel's backoff logic fires
                response.raise_for_status()

            if response.status_code != 200:
                logger.error(f"GitHub API error: {response.status_code} {response.text[:200]}")
                break

            issues = response.json()
            if not issues:
                break

            all_issues.extend(issues)

            # Check Link header for pagination info
            link_header = response.headers.get("link", "")
            if 'rel="next"' not in link_header:
                break

            page += 1

        work_items = []
        for issue in all_issues:
            labels = [label["name"] for label in issue.get("labels", [])]
            task_type = TaskType.IMPLEMENT
            if "agent:plan" in labels or "[Plan]" in issue.get("title", ""):
                task_type = TaskType.PLAN
            elif "bug" in labels:
                task_type = TaskType.BUGFIX

            repo_slug = "/".join(issue["html_url"].split("/")[3:5])

            work_items.append(
                WorkItem(
                    id=str(issue["id"]),
                    issue_number=issue["number"],
                    source_url=issue["html_url"],
                    context_body=issue.get("body") or "",
                    target_repo_slug=repo_slug,
                    task_type=task_type,
                    status=WorkItemStatus.QUEUED,
                    node_id=issue["node_id"],
                )
            )
        return work_items

    async def update_status(
        self, item: WorkItem, status: WorkItemStatus, comment: str | None = None
    ) -> None:
        """Finalize the task state on GitHub with terminal labels and logs."""
        base = self._repo_api_url(item.target_repo_slug)
        url_labels = f"{base}/issues/{item.issue_number}/labels"

        resp = await self._client.delete(f"{url_labels}/{WorkItemStatus.IN_PROGRESS.value}")
        if resp.status_code not in (200, 204, 404, 410):
            logger.error(f"Label cleanup failed: {resp.status_code}")

        # Add the terminal status label and check for failures
        resp = await self._client.post(url_labels, json={"labels": [status.value]})
        if resp.status_code not in (200, 201):
            logger.error(
                f"Failed to set terminal label '{status.value}' on "
                f"#{item.issue_number}: {resp.status_code} - {resp.text[:200]}"
            )
            # Consider raising an exception or returning failure status
            # For now, we log the error but continue to post comment if provided

        if comment:
            safe_comment = scrub_secrets(comment)
            comment_url = f"{base}/issues/{item.issue_number}/comments"
            await self._client.post(comment_url, json={"body": safe_comment})

    # --- Sentinel-specific methods ---

    def _is_claim_stale(self, comment_body: str, comment: dict[str, Any]) -> bool:
        """Check if a sentinel claim is stale based on timestamp.

        A claim is considered stale if:
        1. The claim's start time is older than claim_stale_timeout_secs, OR
        2. We can't parse the timestamp (be conservative and treat as potentially stale)

        Args:
            comment_body: The body text of the claim comment
            comment: The full comment object from GitHub API

        Returns:
            True if the claim should be considered stale and allow re-claiming
        """
        # Try to extract the Start Time from the claim comment
        timestamp_match = re.search(r"\*\*Start Time:\*\*\s*`?([^`\n]+)`?", comment_body)
        if timestamp_match:
            try:
                claim_time_str = timestamp_match.group(1).strip()
                claim_time = datetime.fromisoformat(claim_time_str.replace("Z", "+00:00"))
                elapsed = (datetime.now(UTC) - claim_time).total_seconds()
                if elapsed > self.claim_stale_timeout_secs:
                    return True
            except (ValueError, TypeError) as e:
                logger.debug(f"Could not parse claim timestamp: {e}")
                # Fall back to comment's created_at timestamp
                pass

        # Fallback: use the comment's created_at timestamp from GitHub API
        created_at_str = comment.get("created_at")
        if created_at_str:
            try:
                comment_time = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                elapsed = (datetime.now(UTC) - comment_time).total_seconds()
                if elapsed > self.claim_stale_timeout_secs:
                    return True
            except (ValueError, TypeError) as e:
                logger.debug(f"Could not parse comment created_at: {e}")

        return False

    async def claim_task(self, item: WorkItem, sentinel_id: str, bot_login: str = "") -> bool:
        """Claim a task using assign-then-verify distributed locking.

        Steps:
          1. Attempt to assign bot_login to the issue.
          2. Re-fetch the issue to verify we are the assignee.
          3. Only then update labels and post the claim comment.
        """
        base = self._repo_api_url(item.target_repo_slug)
        url_issue = f"{base}/issues/{item.issue_number}"

        # Step 1: Attempt assignment
        if bot_login:
            resp = await self._client.post(
                f"{url_issue}/assignees",
                json={"assignees": [bot_login]},
            )
            if resp.status_code not in (200, 201):
                logger.warning(f"Failed to assign #{item.issue_number}: {resp.status_code}")
                return False

            # Step 2: Re-fetch and verify assignee (also check for sentinel claim comment)
            verify_resp = await self._client.get(url_issue)
            if verify_resp.status_code == 200:
                issue_data = verify_resp.json()
                assignees = [a["login"] for a in issue_data.get("assignees", [])]
                if bot_login not in assignees:
                    logger.warning(
                        f"Lost race on #{item.issue_number} — "
                        f"assignees are {assignees}, expected {bot_login}"
                    )
                    return False

                # Also verify no other sentinel has claimed via comment marker
                comments_url = f"{url_issue}/comments"
                comments_resp = await self._client.get(comments_url)
                if comments_resp.status_code == 200:
                    comments = comments_resp.json()
                    for comment in comments:
                        body = comment.get("body", "")
                        if "<!-- sentinel-claim:" in body:
                            # Extract sentinel ID from comment
                            match = re.search(r"<!-- sentinel-claim: (.+?) -->", body)
                            if match:
                                existing_sentinel = match.group(1)
                                if existing_sentinel != sentinel_id:
                                    # Check if the claim is stale (older than timeout)
                                    claim_is_stale = self._is_claim_stale(body, comment)
                                    if claim_is_stale:
                                        logger.warning(
                                            f"Found stale claim on #{item.issue_number} from "
                                            f"sentinel {existing_sentinel} — allowing re-claim"
                                        )
                                        # Continue to allow re-claiming
                                        continue
                                    else:
                                        logger.warning(
                                            f"Lost race on #{item.issue_number} — "
                                            f"already claimed by sentinel {existing_sentinel}"
                                        )
                                        return False
            else:
                logger.warning(
                    f"Could not verify assignment for #{item.issue_number}: "
                    f"{verify_resp.status_code}"
                )
                return False

        # Step 3: Post claim comment with sentinel identifier FIRST
        # This ensures other sentinels can see the claim marker before we update labels,
        # preventing a race condition where two sentinels both verify label state
        # and then both proceed with execution.
        comment_url = f"{url_issue}/comments"
        msg = (
            f"🚀 **Sentinel {sentinel_id}** has claimed this task.\n"
            f"- **Sentinel ID:** `{sentinel_id}`\n"
            f"- **Start Time:** {datetime.now(UTC).isoformat()}\n"
            f"- **Environment:** `devcontainer-opencode.sh` initializing...\n\n"
            f"<!-- sentinel-claim: {sentinel_id} -->"
        )
        await self._client.post(comment_url, json={"body": msg})

        # Step 4: Update labels
        url_labels = f"{url_issue}/labels"
        resp = await self._client.delete(f"{url_labels}/{WorkItemStatus.QUEUED.value}")
        if resp.status_code not in (200, 204, 404, 410):
            logger.error(f"Label removal failed: {resp.status_code}")
            return False

        resp = await self._client.post(
            url_labels,
            json={"labels": [WorkItemStatus.IN_PROGRESS.value]},
        )
        if resp.status_code not in (200, 201):
            logger.error(
                f"Failed to add {WorkItemStatus.IN_PROGRESS.value} label to "
                f"#{item.issue_number}: {resp.status_code}"
            )
            return False

        logger.info(f"Successfully claimed Task #{item.issue_number}")
        return True

    async def post_heartbeat(self, item: WorkItem, sentinel_id: str, elapsed_secs: int) -> None:
        """Post a heartbeat comment to keep observers informed."""
        base = self._repo_api_url(item.target_repo_slug)
        comment_url = f"{base}/issues/{item.issue_number}/comments"
        minutes = elapsed_secs // 60
        msg = (
            f"💓 **Heartbeat** — Sentinel {sentinel_id} still working.\n"
            f"- **Elapsed:** {minutes}m\n"
            f"- **Timestamp:** {datetime.now(UTC).isoformat()}"
        )
        try:
            await self._client.post(comment_url, json={"body": msg})
        except Exception as exc:
            logger.warning(f"Heartbeat post failed: {exc}")

    async def requeue_with_feedback(
        self, item: WorkItem, feedback_body: str, reason: str = "Reviewer feedback"
    ) -> bool:
        """Requeue a task with reviewer feedback included.

        This method is used when a task needs to be re-queued with additional
        feedback (e.g., from a PR review). The feedback is posted as a comment
        and the task is marked as queued for re-processing.

        Args:
            item: The WorkItem to requeue
            feedback_body: The reviewer feedback to include
            reason: Reason for requeuing (default: "Reviewer feedback")

        Returns:
            True if requeue was successful, False otherwise
        """
        base = self._repo_api_url(item.target_repo_slug)
        url_labels = f"{base}/issues/{item.issue_number}/labels"

        # Remove any terminal status labels
        for status in (WorkItemStatus.SUCCESS, WorkItemStatus.ERROR, WorkItemStatus.IN_PROGRESS):
            resp = await self._client.delete(f"{url_labels}/{status.value}")
            if resp.status_code not in (200, 204, 404, 410):
                logger.debug(f"Label cleanup for {status.value}: {resp.status_code}")

        # Add queued label
        resp = await self._client.post(url_labels, json={"labels": [WorkItemStatus.QUEUED.value]})
        if resp.status_code not in (200, 201):
            logger.error(f"Failed to requeue #{item.issue_number}: {resp.status_code}")
            return False

        # Post feedback as a comment so the agent knows what corrections were requested
        safe_feedback = scrub_secrets(feedback_body)
        comment_url = f"{base}/issues/{item.issue_number}/comments"
        msg = (
            f"🔄 **Task Requeued** — {reason}\n\n"
            f"### Reviewer Feedback\n\n{safe_feedback}\n\n"
            f"---\n*Please address the feedback above and resubmit.*"
        )
        await self._client.post(comment_url, json={"body": msg})

        logger.info(f"Requeued #{item.issue_number} with reviewer feedback")
        return True
