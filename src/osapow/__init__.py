"""
OS-APOW (Orchestration System for AI-Powered Operations Workflow)

A paradigm shift from Interactive AI Coding to Headless Agentic Orchestration.
Transforms GitHub Issues into "Execution Orders" autonomously fulfilled by
specialized AI agents.

See: OS-APOW Architecture Guide v3.2
"""

__version__ = "0.1.0"
__author__ = "Intel Agency"

from osapow.models import TaskType, WorkItem, WorkItemStatus, scrub_secrets
from osapow.queue import GitHubQueue, ITaskQueue

__all__ = [
    "__version__",
    "TaskType",
    "WorkItem",
    "WorkItemStatus",
    "scrub_secrets",
    "GitHubQueue",
    "ITaskQueue",
]
