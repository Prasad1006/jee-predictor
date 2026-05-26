"""Gemini API key rotation and load balancing.

Distributes requests across multiple keys to avoid hitting free-tier limits.
Implements cooldown, retry logic, and automatic failover.
"""
from __future__ import annotations

import os
import re
import time
from datetime import datetime, timedelta
from typing import Optional


class KeyRotationManager:
    """Manages API key rotation with cooldown and load balancing."""

    def __init__(self, max_keys: int = 20):
        self.max_keys = max_keys
        self.keys = self._load_keys()
        self.key_stats = {key: {"requests": 0, "errors": 0, "cooldown_until": 0} for key in self.keys}
        self.current_index = 0

    def _load_keys(self) -> list[str]:
        """Load API keys from environment (GEMINI_API_KEYS, GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.)."""
        keys = []
        seen = set()

        def add_key(value: str) -> None:
            normalized = value.strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                keys.append(normalized)

        # Support comma/semicolon/newline-separated list of keys in one env variable
        raw_keys = os.getenv("GEMINI_API_KEYS", "").strip()
        if raw_keys:
            for key in re.split(r"[\n\r,;]+", raw_keys):
                add_key(key)

        # Try individual key env vars next
        for i in range(1, self.max_keys + 1):
            add_key(os.getenv(f"GEMINI_API_KEY_{i}", ""))

        # Fallback to single GEMINI_API_KEY
        if not keys:
            try:
                from django.conf import settings
                key = getattr(settings, "GEMINI_API_KEY", "") or ""
                if key:
                    keys.append(key.strip())
            except Exception:
                pass

            if not keys:
                key = os.getenv("GEMINI_API_KEY", "").strip()
                if key:
                    keys.append(key)

        return keys if keys else [""]

    def get_next_key(self) -> str:
        """Get the next available API key using round-robin with cooldown checks."""
        if not self.keys or all(k == "" for k in self.keys):
            return ""
        
        now = time.time()
        attempts = 0
        max_attempts = len(self.keys)
        
        while attempts < max_attempts:
            key = self.keys[self.current_index % len(self.keys)]
            stats = self.key_stats.get(key, {})
            cooldown_until = stats.get("cooldown_until", 0)
            
            # Skip if in cooldown
            if now < cooldown_until:
                self.current_index += 1
                attempts += 1
                continue
            
            # Key is available
            self.current_index += 1
            stats["requests"] = stats.get("requests", 0) + 1
            return key
        
        # All keys in cooldown, return the one with shortest remaining cooldown
        available_key = min(
            self.keys,
            key=lambda k: self.key_stats.get(k, {}).get("cooldown_until", 0),
        )
        return available_key

    def mark_success(self, key: str) -> None:
        """Mark a key as successful (no cooldown needed)."""
        if key not in self.key_stats:
            self.key_stats[key] = {"requests": 0, "errors": 0, "cooldown_until": 0}
        self.key_stats[key]["requests"] = self.key_stats[key].get("requests", 0) + 1

    def mark_error(self, key: str, error_type: str = "rate_limit", cooldown_seconds: int = 60) -> None:
        """Mark a key as having an error and apply cooldown.
        
        Args:
            key: API key that failed
            error_type: Type of error ("rate_limit", "auth", "invalid", "network")
            cooldown_seconds: How long to cooldown this key
        """
        if key not in self.key_stats:
            self.key_stats[key] = {"requests": 0, "errors": 0, "cooldown_until": 0}
        
        stats = self.key_stats[key]
        stats["errors"] = stats.get("errors", 0) + 1
        
        # Exponential backoff based on error count
        if error_type == "rate_limit":
            backoff = min(300, 60 * (2 ** (stats.get("errors", 1) - 1)))
        elif error_type == "auth":
            backoff = 3600  # 1 hour for auth errors
        elif error_type == "invalid":
            backoff = 86400  # 24 hours for invalid keys
        else:
            backoff = cooldown_seconds
        
        stats["cooldown_until"] = time.time() + backoff

    def get_stats(self) -> dict:
        """Get current statistics about all keys."""
        return {
            "total_keys": len(self.keys),
            "active_keys": len([k for k in self.keys if k != ""]),
            "key_stats": self.key_stats,
            "request_total": sum(s.get("requests", 0) for s in self.key_stats.values()),
            "error_total": sum(s.get("errors", 0) for s in self.key_stats.values()),
        }

    def reset_key(self, key: str) -> None:
        """Reset cooldown for a specific key."""
        if key in self.key_stats:
            self.key_stats[key]["cooldown_until"] = 0


# Global manager instance
_manager: Optional[KeyRotationManager] = None


def get_key_manager() -> KeyRotationManager:
    """Get or create the global key rotation manager."""
    global _manager
    if _manager is None:
        _manager = KeyRotationManager()
    return _manager


def get_api_key() -> str:
    """Get the next available API key for a request."""
    manager = get_key_manager()
    return manager.get_next_key()


def mark_key_error(key: str, error_type: str = "rate_limit") -> None:
    """Mark an API key as having an error."""
    manager = get_key_manager()
    manager.mark_error(key, error_type)


def mark_key_success(key: str) -> None:
    """Mark an API key as successful."""
    manager = get_key_manager()
    manager.mark_success(key)
