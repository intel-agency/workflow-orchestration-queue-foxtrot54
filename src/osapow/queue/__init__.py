"""Queue package for OS-APOW."""

from .github_queue import GitHubQueue, ITaskQueue

__all__ = ["GitHubQueue", "ITaskQueue"]
