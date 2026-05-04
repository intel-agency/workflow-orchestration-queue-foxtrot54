"""Notifier package for OS-APOW."""

from .service import WebhookNotifier, create_app

__all__ = ["create_app", "WebhookNotifier"]
