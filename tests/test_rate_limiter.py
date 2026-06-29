"""
Tests for the Telegram bot rate limiter (_check_rate_limit).
"""
import time
import pytest


def _get_check_fn(window=60, max_req=10):
    """Import and re-initialise the rate limiter state for each test."""
    import importlib
    import sys

    # Patch env before import so constants are picked up
    import os
    os.environ["RATE_LIMIT_WINDOW"] = str(window)
    os.environ["RATE_LIMIT_MAX"] = str(max_req)
    os.environ["TELEGRAM_BOT_TOKEN"] = "fake:token"
    os.environ.setdefault("ANTHROPIC_API_KEY", "fake-key")

    # Re-import to pick up fresh module-level state
    if "run_agent_telegram" in sys.modules:
        del sys.modules["run_agent_telegram"]

    import run_agent_telegram as bot_module
    # Reset shared state
    bot_module._rl_timestamps.clear()
    return bot_module._check_rate_limit


def test_first_request_allowed():
    fn = _get_check_fn()
    assert fn(chat_id=1) is True


def test_requests_within_limit_allowed():
    fn = _get_check_fn(window=60, max_req=5)
    for _ in range(5):
        assert fn(chat_id=2) is True


def test_request_over_limit_blocked():
    fn = _get_check_fn(window=60, max_req=3)
    fn(chat_id=3)
    fn(chat_id=3)
    fn(chat_id=3)
    assert fn(chat_id=3) is False  # 4th → blocked


def test_different_chats_independent():
    fn = _get_check_fn(window=60, max_req=2)
    fn(chat_id=10)
    fn(chat_id=10)
    # chat 10 is now at limit
    assert fn(chat_id=10) is False
    # chat 11 is independent — should still be allowed
    assert fn(chat_id=11) is True


def test_expired_timestamps_do_not_count(monkeypatch):
    fn = _get_check_fn(window=5, max_req=2)

    import run_agent_telegram as bot_module

    # Manually inject old timestamps (outside the window)
    old_time = time.time() - 10  # 10 sec ago, window is 5 sec
    bot_module._rl_timestamps[20] = [old_time, old_time]

    # Should be allowed — old timestamps evicted
    assert fn(chat_id=20) is True
