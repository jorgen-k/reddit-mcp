"""fetch_json is a Reddit tool: non-Reddit URLs are opt-in via an env flag.

A general-purpose fetch escape hatch inside a Reddit server gets picked by the
model at the wrong moments, so arbitrary hosts stay off unless the operator
turns them on. No network: the HTTP client is faked.
"""

from __future__ import annotations

import asyncio

import pytest

import server


class FakeResponse:
    def __init__(self, payload, status_code=200, headers=None):
        self._payload = payload
        self.status_code = status_code
        self.headers = headers or {"content-type": "application/json"}
        self.url = "http://example.com/data"
        self.text = "{}"

    @property
    def is_success(self):
        return 200 <= self.status_code < 300

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


class FakeClient:
    """Stands in for httpx.AsyncClient, recording every URL it was asked for."""

    requested: list[str] = []

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, params=None):
        FakeClient.requested.append(url)
        return FakeResponse({"ok": True})


@pytest.fixture
def fake_http(monkeypatch):
    FakeClient.requested = []
    monkeypatch.setattr(server.httpx, "AsyncClient", FakeClient)
    return FakeClient


def test_non_reddit_url_refused_by_default(monkeypatch, fake_http):
    monkeypatch.delenv("REDDIT_MCP_ALLOW_ANY_URL", raising=False)
    with pytest.raises(ValueError):
        asyncio.run(server.fetch_json("https://example.com/data"))
    assert fake_http.requested == []  # refused before any request went out


def test_non_reddit_url_allowed_when_flag_set(monkeypatch, fake_http):
    monkeypatch.setenv("REDDIT_MCP_ALLOW_ANY_URL", "1")
    result = asyncio.run(server.fetch_json("https://example.com/data"))
    assert result["data"] == {"ok": True}
    assert fake_http.requested == ["https://example.com/data"]


def test_reddit_url_works_without_the_flag(monkeypatch, fake_http):
    monkeypatch.delenv("REDDIT_MCP_ALLOW_ANY_URL", raising=False)
    captured = {}

    async def fake_fetch_feed(url, params=None):
        captured["url"] = url
        return ("r/python", [])

    monkeypatch.setattr(server, "_fetch_feed", fake_fetch_feed)
    result = asyncio.run(server.fetch_json("https://www.reddit.com/r/python"))
    assert captured["url"] == "https://www.reddit.com/r/python/.rss"
    assert result["feed_title"] == "r/python"


@pytest.mark.parametrize("value", ["0", "false", "no", ""])
def test_flag_off_values_keep_non_reddit_refused(monkeypatch, fake_http, value):
    monkeypatch.setenv("REDDIT_MCP_ALLOW_ANY_URL", value)
    with pytest.raises(ValueError):
        asyncio.run(server.fetch_json("https://example.com/data"))
    assert fake_http.requested == []
