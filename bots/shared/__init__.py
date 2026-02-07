"""
Shared components for Zulip news bots.

This package provides a base class and utilities for building news aggregator
bots that post to Zulip.
"""

from .base_bot import BaseNewsBot

__all__ = ["BaseNewsBot"]
