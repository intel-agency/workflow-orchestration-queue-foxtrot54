"""
OS-APOW Webhook Notifier Service

FastAPI-based webhook receiver for GitHub events. The "Ear" of the
4-Pillar Architecture that handles secure webhook ingestion and
intelligent event triage.

See: OS-APOW Architecture Guide v3.2
"""

import hashlib
import hmac
import logging
import os

from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

from osapow.models import TaskType, WorkItem, WorkItemStatus
from osapow.queue import GitHubQueue

logger = logging.getLogger("OS-APOW")


class WebhookPayload(BaseModel):
    """Simplified webhook payload model."""

    action: str
    issue: dict | None = None
    repository: dict | None = None


class WebhookNotifier:
    """Handles GitHub webhook events and queues work items."""

    def __init__(self, queue: GitHubQueue, webhook_secret: str = ""):
        self.queue = queue
        self.webhook_secret = webhook_secret

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify HMAC SHA256 webhook signature."""
        if not self.webhook_secret:
            return True  # Skip verification if no secret configured

        expected = (
            "sha256="
            + hmac.new(
                self.webhook_secret.encode(),
                payload,
                hashlib.sha256,
            ).hexdigest()
        )

        return hmac.compare_digest(expected, signature)

    def parse_work_item(self, payload: dict) -> WorkItem | None:
        """Parse a GitHub webhook payload into a WorkItem."""
        issue = payload.get("issue") or payload.get("pull_request")
        if not issue:
            return None

        repo = payload.get("repository", {})
        repo_slug = repo.get("full_name", "")

        # Determine task type from labels
        labels = [label.get("name", "") for label in issue.get("labels", [])]
        task_type = TaskType.IMPLEMENT
        if "agent:plan" in labels or "[Plan]" in issue.get("title", ""):
            task_type = TaskType.PLAN
        elif "bug" in labels:
            task_type = TaskType.BUGFIX

        return WorkItem(
            id=str(issue.get("id", "")),
            issue_number=issue.get("number", 0),
            source_url=issue.get("html_url", ""),
            context_body=issue.get("body") or "",
            target_repo_slug=repo_slug,
            task_type=task_type,
            status=WorkItemStatus.QUEUED,
            node_id=issue.get("node_id", ""),
        )


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="OS-APOW Webhook Notifier",
        description="Webhook receiver for GitHub events",
        version="0.1.0",
    )

    # Initialize queue and notifier
    token = os.environ.get("GITHUB_TOKEN", "")
    webhook_secret = os.environ.get("WEBHOOK_SECRET", "")
    queue = GitHubQueue(token=token)
    notifier = WebhookNotifier(queue=queue, webhook_secret=webhook_secret)

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "osapow-notifier"}

    @app.post("/webhook/github")
    async def handle_github_webhook(
        request: Request,
        x_hub_signature_256: str = Header(default=""),
        x_github_event: str = Header(default=""),
    ):
        """Handle incoming GitHub webhooks."""
        payload_bytes = await request.body()

        # Verify signature
        if not notifier.verify_signature(payload_bytes, x_hub_signature_256):
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse payload
        try:
            payload = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        # Only process relevant events
        if x_github_event not in ("issues", "issue_comment", "pull_request"):
            return {"status": "ignored", "event": x_github_event}

        action = payload.get("action", "")
        if action not in ("opened", "labeled", "reopened"):
            return {"status": "ignored", "action": action}

        # Parse and queue work item
        work_item = notifier.parse_work_item(payload)
        if not work_item:
            return {"status": "ignored", "reason": "No valid work item"}

        success = await queue.add_to_queue(work_item)
        if success:
            logger.info(f"Queued work item #{work_item.issue_number}")
            return {"status": "queued", "issue": work_item.issue_number}
        else:
            raise HTTPException(status_code=500, detail="Failed to queue work item")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Clean up resources on shutdown."""
        await queue.close()

    return app


# For uvicorn
app = create_app()
