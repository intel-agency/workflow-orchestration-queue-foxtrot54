"""
OS-APOW Entry Point

Run the sentinel orchestrator with: python -m osapow

Environment Variables:
    GITHUB_TOKEN: GitHub App installation token
    GITHUB_ORG: Target organization name
    GITHUB_REPO: Target repository name
    SENTINEL_BOT_LOGIN: Bot account login for assign-then-verify locking
    SENTINEL_POLL_INTERVAL: Polling interval in seconds (default: 60)
    HEARTBEAT_INTERVAL: Heartbeat interval in seconds (default: 300)
"""

from osapow.sentinel.orchestrator import run_main

if __name__ == "__main__":
    run_main()
