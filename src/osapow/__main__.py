"""
OS-APOW Entry Point

Run the sentinel orchestrator with: python -m osapow

Environment Variables:
    GITHUB_TOKEN: GitHub App installation token
    GITHUB_ORG: Target organization name
    GITHUB_REPO: Target repository name
    SENTINEL_BOT_LOGIN: Bot account login for assign-then-verify locking
"""

import asyncio
import logging
import os

from osapow.sentinel.orchestrator import SentinelOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("OS-APOW")


def main():
    """Main entry point."""
    token = os.environ.get("GITHUB_TOKEN", "")
    org = os.environ.get("GITHUB_ORG", "")
    repo = os.environ.get("GITHUB_REPO", "")
    bot_login = os.environ.get("SENTINEL_BOT_LOGIN", "")

    if not all([token, org, repo]):
        logger.error(
            "Missing required environment variables: "
            "GITHUB_TOKEN, GITHUB_ORG, GITHUB_REPO"
        )
        raise SystemExit(1)

    sentinel = SentinelOrchestrator(
        token=token,
        org=org,
        repo=repo,
        bot_login=bot_login,
    )

    asyncio.run(sentinel.start())


if __name__ == "__main__":
    main()
