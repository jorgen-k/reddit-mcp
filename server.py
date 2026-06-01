#!/usr/bin/env python3
"""Local MCP server that fetches and refines Reddit (and other JSON) content.

Reddit gates its Data API (new apps require a moderation use case + approval)
and blocks anonymous ``.json`` access, but it still publishes public **Atom/RSS
feeds** for reading content. These tools fetch those feeds and trim them to the
useful fields. No authentication, account, or app registration required.

Feeds carry title, author, link, timestamp, and full post/comment text — but
NOT scores, upvote ratios, or comment counts (those only exist in the gated API).

The generic ``fetch_json`` tool also works for non-Reddit services that expose
JSON via the ``.json`` convention.
"""

from __future__ import annotations

import html
import os
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit, urlunsplit

import httpx
from mcp.server.fastmcp import FastMCP

# Feed readers send their own User-Agent; Reddit serves RSS to them normally.
USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "reddit-mcp/1.0 (personal RSS reader)")
REDDIT_BASE = "https://www.reddit.com"
ATOM = {"a": "http://www.w3.org/2005/Atom"}
TIMEOUT = 30.0
TEXT_MAX = 2000

mcp = FastMCP("reddit")


# --------------------------------------------------------------------------- #
# Fetch + parse
# --------------------------------------------------------------------------- #
async def _fetch_feed(url: str, params: dict | None = None) -> tuple[str | None, list[dict]]:
    """GET an Atom feed and return (feed_title, [refined entries])."""
    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient(
        timeout=TIMEOUT, follow_redirects=True, headers=headers
    ) as client:
        resp = await client.get(url, params=params)
    if resp.status_code == 429:
        raise RuntimeError(
            "Reddit rate-limited this request (HTTP 429). Wait a bit and retry."
        )
    resp.raise_for_status()
    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        raise RuntimeError(f"Could not parse feed (not valid Atom XML): {e}")
    feed_title = root.findtext("a:title", namespaces=ATOM)
    entries = [_refine_entry(e) for e in root.findall("a:entry", ATOM)]
    return feed_title, entries


# --------------------------------------------------------------------------- #
# Refinement helpers
# --------------------------------------------------------------------------- #
def _truncate(text: str | None, limit: int = TEXT_MAX) -> str | None:
    if not text:
        return text
    if len(text) <= limit:
        return text
    return text[:limit] + f"… [truncated, {len(text)} chars total]"


def _html_to_text(raw: str | None, limit: int = TEXT_MAX) -> str | None:
    """Convert the HTML in a feed <content> to readable plain text."""
    if not raw:
        return raw
    s = re.sub(r"(?is)<(script|style).*?</\1>", "", raw)
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</p>", "\n\n", s)
    s = re.sub(r"(?s)<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"\n{3,}", "\n\n", s).strip()
    return _truncate(s, limit)


def _refine_entry(entry: ET.Element) -> dict:
    """Reduce an Atom entry (post or comment) to the useful fields."""
    full_id = entry.findtext("a:id", default="", namespaces=ATOM)
    kind, _, short_id = full_id.partition("_")  # e.g. "t3_abc123"
    link_el = entry.find("a:link", ATOM)
    category = entry.find("a:category", ATOM)
    return {
        "id": short_id or full_id,
        "type": {"t3": "post", "t1": "comment"}.get(kind, kind or None),
        "title": entry.findtext("a:title", namespaces=ATOM),
        "author": entry.findtext("a:author/a:name", namespaces=ATOM),
        "subreddit": category.get("term") if category is not None else None,
        "published": entry.findtext("a:published", namespaces=ATOM),
        "updated": entry.findtext("a:updated", namespaces=ATOM),
        "link": link_el.get("href") if link_el is not None else None,
        "text": _html_to_text(entry.findtext("a:content", namespaces=ATOM)),
    }


def _is_reddit_host(netloc: str) -> bool:
    host = netloc.lower().split(":")[0]
    return host == "reddit.com" or host.endswith(".reddit.com")


# --------------------------------------------------------------------------- #
# Tools
# --------------------------------------------------------------------------- #
@mcp.tool()
async def browse_subreddit(
    subreddit: str,
    sort: str = "hot",
    time_filter: str = "day",
    limit: int = 25,
) -> dict:
    """List posts from a subreddit (via its public RSS feed).

    Note: RSS does not include scores, upvote ratios, or comment counts.

    Args:
        subreddit: Subreddit name, with or without the "r/" prefix.
        sort: One of hot, new, top, rising, controversial.
        time_filter: For top/controversial — hour, day, week, month, year, all.
        limit: Number of posts (1-100).
    """
    sub = subreddit.strip().removeprefix("r/").strip("/")
    sort = sort.strip().lower()
    limit = max(1, min(int(limit), 100))
    params = {"limit": limit}
    if sort in ("top", "controversial"):
        params["t"] = time_filter
    title, entries = await _fetch_feed(f"{REDDIT_BASE}/r/{sub}/{sort}/.rss", params)
    return {
        "subreddit": sub,
        "sort": sort,
        "feed_title": title,
        "count": len(entries),
        "posts": entries,
    }


@mcp.tool()
async def get_post(url: str, comment_limit: int = 50) -> dict:
    """Fetch a single post and its comments (via the post's RSS feed).

    Comments come back as a flat list (RSS doesn't expose the reply tree), and
    scores/vote counts are not available.

    Args:
        url: A Reddit post URL or permalink (e.g.
            https://www.reddit.com/r/python/comments/abc123/title/ or
            /r/python/comments/abc123/title/).
        comment_limit: Max comments to return.
    """
    u = url.strip()
    path = u if u.startswith("/") else urlsplit(u).path
    path = path.rstrip("/")
    if path.endswith("/.rss"):
        path = path[: -len("/.rss")]
    feed_url = f"{REDDIT_BASE}{path}/.rss"

    _, entries = await _fetch_feed(feed_url, {"limit": comment_limit})
    posts = [e for e in entries if e["type"] == "post"]
    comments = [e for e in entries if e["type"] == "comment"][:comment_limit]
    if not posts and not comments:
        raise RuntimeError("No content found — is this a valid post URL?")

    return {
        "post": posts[0] if posts else None,
        "comment_count": len(comments),
        "comments": comments,
    }


@mcp.tool()
async def search_reddit(
    query: str,
    subreddit: str | None = None,
    sort: str = "relevance",
    time_filter: str = "all",
    limit: int = 25,
) -> dict:
    """Search Reddit, optionally scoped to a subreddit (via the search RSS feed).

    Note: RSS results do not include scores or comment counts.

    Args:
        query: Search terms.
        subreddit: Restrict to this subreddit (with or without "r/").
        sort: relevance, hot, top, new, comments.
        time_filter: hour, day, week, month, year, all.
        limit: Number of results (1-100).
    """
    limit = max(1, min(int(limit), 100))
    params = {"q": query, "sort": sort, "t": time_filter, "limit": limit}
    if subreddit:
        sub = subreddit.strip().removeprefix("r/").strip("/")
        params["restrict_sr"] = "1"
        url = f"{REDDIT_BASE}/r/{sub}/search.rss"
    else:
        url = f"{REDDIT_BASE}/search.rss"
    title, entries = await _fetch_feed(url, params)
    return {"query": query, "count": len(entries), "results": entries}


@mcp.tool()
async def fetch_json(url: str) -> dict:
    """Fetch a URL as structured data.

    For Reddit URLs (any feed type — user, domain, multireddit, etc.) this
    fetches the ``.rss`` feed and returns refined entries. For other services it
    tries the URL as-is, falling back to the ``.json`` convention if the plain
    response isn't JSON.

    Args:
        url: The URL to fetch.
    """
    parts = urlsplit(url.strip())

    if _is_reddit_host(parts.netloc):
        path = parts.path.rstrip("/")
        if not path.endswith(".rss"):
            path += "/.rss"
        target = urlunsplit((parts.scheme, parts.netloc, path, parts.query, ""))
        title, entries = await _fetch_feed(target)
        return {"url": target, "feed_title": title, "count": len(entries), "entries": entries}

    # Non-Reddit: try the URL as given, then fall back to the .json convention.
    async with httpx.AsyncClient(
        timeout=TIMEOUT, follow_redirects=True, headers={"User-Agent": USER_AGENT}
    ) as client:
        resp = await client.get(url.strip())
        if resp.is_success:
            try:
                return {"url": str(resp.url), "data": resp.json()}
            except ValueError:
                pass  # not JSON — try the .json fallback below

        path = parts.path.rstrip("/")
        if not path.endswith(".json"):
            fallback = urlunsplit(
                (parts.scheme, parts.netloc, path + ".json", parts.query, "")
            )
            resp = await client.get(fallback)

    resp.raise_for_status()
    try:
        return {"url": str(resp.url), "data": resp.json()}
    except ValueError:
        return {
            "url": str(resp.url),
            "note": f"Response was not JSON (content-type: "
            f"{resp.headers.get('content-type', '')}).",
            "text": _truncate(resp.text, 5000),
        }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
