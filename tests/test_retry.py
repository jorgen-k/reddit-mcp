"""Unit tests for the 429 retry/backoff and throttle layer in server.py.

No network and no real sleeping: the HTTP client is faked, asyncio.sleep is
recorded instead of awaited, and time.monotonic is pinned where timing matters.
"""

from __future__ import annotations

import asyncio

import pytest

import server


class FakeResponse:
    def __init__(self, status_code: int, headers: dict | None = None):
        self.status_code = status_code
        self.headers = headers or {}


class FakeClient:
    """Returns the queued responses in order, counting calls."""

    def __init__(self, responses: list):
        self._responses = [
            r if isinstance(r, FakeResponse) else FakeResponse(r) for r in responses
        ]
        self.calls = 0

    async def get(self, url, params=None):
        self.calls += 1
        return self._responses.pop(0)


@pytest.fixture
def record_sleep(monkeypatch):
    """Record asyncio.sleep durations without waiting; jitter pinned to 0.5."""
    slept: list[float] = []

    async def fake_sleep(delay):
        slept.append(delay)

    monkeypatch.setattr(server.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(server.random, "random", lambda: 0.5)
    return slept


@pytest.fixture
def no_throttle(monkeypatch):
    """Disable the inter-request throttle so only backoff sleeps are recorded."""

    async def noop():
        return None

    monkeypatch.setattr(server, "_throttle", noop)


def test_retry_then_success(record_sleep, no_throttle):
    client = FakeClient([429, 429, 200])
    resp = asyncio.run(server._get_with_retry(client, "http://x"))
    assert resp.status_code == 200
    assert client.calls == 3
    assert record_sleep == [2.5, 4.5]  # two backoff sleeps before the 200


def test_exhaustion_raises_with_attempt_count(record_sleep, no_throttle):
    client = FakeClient([FakeResponse(429)] * 20)
    with pytest.raises(RuntimeError) as exc:
        asyncio.run(server._get_with_retry(client, "http://x"))
    # 1 initial attempt + MAX_RETRIES retries
    assert client.calls == server.MAX_RETRIES + 1
    assert f"after {server.MAX_RETRIES + 1} attempt(s)" in str(exc.value)


def test_honors_retry_after(record_sleep, no_throttle):
    client = FakeClient([FakeResponse(429, {"Retry-After": "7"}), FakeResponse(200)])
    resp = asyncio.run(server._get_with_retry(client, "http://x"))
    assert resp.status_code == 200
    assert record_sleep == [7.0]  # header value overrides the backoff formula


def test_exhaustion_reports_last_retry_after(record_sleep, no_throttle):
    client = FakeClient([FakeResponse(429, {"Retry-After": "3"})] * 20)
    with pytest.raises(RuntimeError) as exc:
        asyncio.run(server._get_with_retry(client, "http://x"))
    assert "last Retry-After was 3s" in str(exc.value)


def test_backoff_doubles_with_jitter(record_sleep, no_throttle):
    client = FakeClient([FakeResponse(429)] * 20)
    with pytest.raises(RuntimeError):
        asyncio.run(server._get_with_retry(client, "http://x"))
    # base * 2**n + jitter(0.5), one sleep per retry (no sleep after the last)
    expected = [server.BACKOFF_BASE * (2**n) + 0.5 for n in range(server.MAX_RETRIES)]
    assert record_sleep == expected


def test_no_retry_on_success(record_sleep, no_throttle):
    client = FakeClient([200])
    resp = asyncio.run(server._get_with_retry(client, "http://x"))
    assert resp.status_code == 200
    assert client.calls == 1
    assert record_sleep == []


@pytest.mark.parametrize(
    "value, expected",
    [("7", 7.0), ("0", 0.0), (None, None), ("", None), ("Wed, 21 Oct 2025 07:28:00 GMT", None)],
)
def test_parse_retry_after(value, expected):
    assert server._parse_retry_after(value) == expected


def test_throttle_waits_for_min_interval(monkeypatch):
    slept: list[float] = []

    async def fake_sleep(delay):
        slept.append(delay)

    monkeypatch.setattr(server.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(server.time, "monotonic", lambda: 100.3)
    monkeypatch.setattr(server, "_last_request_at", 100.0)

    asyncio.run(server._throttle())
    # MIN_INTERVAL (1.0) minus the 0.3s already elapsed since the last request
    assert slept == [pytest.approx(server.MIN_INTERVAL - 0.3)]


def test_throttle_no_wait_when_idle(monkeypatch):
    slept: list[float] = []

    async def fake_sleep(delay):
        slept.append(delay)

    monkeypatch.setattr(server.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(server.time, "monotonic", lambda: 1000.0)
    monkeypatch.setattr(server, "_last_request_at", 0.0)

    asyncio.run(server._throttle())
    assert slept == []  # plenty of time has passed; no need to wait
