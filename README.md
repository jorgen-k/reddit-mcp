# reddit-mcp

<!-- mcp-name: io.github.jorgen-k/reddit-mcp -->

A small **local MCP server** that lets Claude read Reddit (and other JSON
endpoints), refining the responses down to the fields that matter.

> **How it reaches Reddit:** Reddit gates its Data API (new apps require a
> moderation use case + approval) and blocks anonymous `.json` access, but it
> still publishes public **Atom/RSS feeds** for reading content. This server
> uses those — so it needs **no account, no app, no API key, no login**.
>
> Trade-off: RSS carries title, author, link, timestamp, and full post/comment
> text, but **not** scores, upvote ratios, or comment counts (those only live in
> the gated API).

## Tools

| Tool | What it does |
|------|--------------|
| `browse_subreddit(subreddit, sort="hot", time_filter="day", limit=25)` | Posts from a subreddit (`hot`/`new`/`top`/`rising`/`controversial`). |
| `get_post(url, comment_limit=50)` | A post plus its comments (flat list — RSS doesn't expose the reply tree). |
| `search_reddit(query, subreddit=None, sort="relevance", time_filter="all", limit=25)` | Search Reddit, optionally scoped to one subreddit. |
| `fetch_json(url)` | Reddit URLs → the `.rss` feed (refined); other URLs → fetched as-is, falling back to the `.json` convention. |

## Requirements

- [`uv`](https://docs.astral.sh/uv/) — handles Python + deps. `uv run server.py`
  provisions an isolated env from `pyproject.toml` on first run. No other setup.

## Install

`reddit-rss-mcp` is published on PyPI (the plain `reddit-mcp` name belongs to an
unrelated project). Three ways to install it, easiest first.

### From PyPI (recommended)

`uvx reddit-rss-mcp` fetches and runs the published package for you, no clone
needed. This is the preferred install.

**Claude Code:**

```sh
claude mcp add reddit -s user -- uvx reddit-rss-mcp
```

**Claude Desktop — one-click:** download `reddit-rss-mcp.mcpb` from the
[latest release](https://github.com/jorgen-k/reddit-mcp/releases/latest) and drag
it into **Settings → Extensions**. No JSON editing, no absolute paths. (It runs
`uvx reddit-rss-mcp`, so it needs [`uv`](https://docs.astral.sh/uv/) on your PATH.)

**Claude Desktop & Cowork — manual config** (fallback if you'd rather not use the
extension; add to `claude_desktop_config.json` using the absolute path from
`which uvx`, then follow the quit/relaunch steps below):

```json
{
  "mcpServers": {
    "reddit": {
      "command": "/absolute/path/to/uvx",
      "args": ["reddit-rss-mcp"]
    }
  }
}
```

### From GitHub (latest `main`, no clone)

To run unreleased changes, point `uvx` at the repo and the `reddit-rss-mcp` entry
point. Append `@v1.1.1` (or any tag) to pin a release instead of tracking `main`:

```sh
claude mcp add reddit -s user -- uvx --from git+https://github.com/jorgen-k/reddit-mcp reddit-rss-mcp
```

### From a local clone

Prefer this if you want to edit the code. Clone it somewhere first:

```sh
git clone https://github.com/jorgen-k/reddit-mcp.git
cd reddit-mcp
```

#### Claude Code

```sh
claude mcp add reddit -s user -- uv --directory "$(pwd)" run server.py
```

Verify with `claude mcp list` (should show `reddit: ✓ Connected`). If Claude
can't find `uv`, use its absolute path (`which uv`) instead of bare `uv`.

#### Claude Desktop & Cowork

Both use the same config file:
`~/Library/Application Support/Claude/claude_desktop_config.json`. Add a
`mcpServers` entry using **absolute paths** — the app doesn't inherit your shell
`PATH`. Get the values with `which uv` and `pwd`:

```json
{
  "mcpServers": {
    "reddit": {
      "command": "/absolute/path/to/uv",
      "args": ["--directory", "/absolute/path/to/reddit-mcp", "run", "server.py"]
    }
  }
}
```

If the file already has other top-level keys, add `mcpServers` alongside them —
don't overwrite the file.

Then:

1. **Fully quit the app** — `Cmd+Q`, not just closing the window. The running
   app rewrites this file, so an edit made while it's open can be discarded.
2. **Relaunch.** It may take a couple of restarts before the server registers.
3. **Grant permission** when the app prompts to run the server.

The Reddit tools then appear in the app.

> **Don't use a Custom Connector** (the "add server by URL" option) for a local
> server — those are dialed from Anthropic's cloud and can't reach `localhost`,
> no matter the cert or tunnel. The config-file method above spawns the server
> locally on your machine, which is what works.

### Updating after a code change

The server runs as a long-lived process that's spawned once when the client
connects. Editing `server.py` does **not** hot-reload it — the running process
keeps the old code until it's restarted. After any change, restart the server so
the new code takes effect:

- **Claude Code:** run `/mcp`, select `reddit`, and reconnect it (or restart
  Claude Code).
- **Claude Desktop & Cowork:** fully quit the app (`Cmd+Q`) and relaunch.

## Notes

- Read-only, public content only.
- No scores/vote counts/comment counts (RSS limitation). For those you'd need
  Reddit's Data API, which now requires a moderation use case + approval.
- Be considerate with request volume — these are public feeds.

### Rate limiting

Reddit throttles its unauthenticated RSS feeds aggressively. On an HTTP 429 the
server transparently retries with backoff (honoring the `Retry-After` header
when present, otherwise exponential backoff with jitter) and only surfaces an
error after retries are exhausted. It also keeps a small minimum gap between
outbound requests to avoid tripping the limit in the first place. All tools
share this behavior. A 429 is retried up to 7 times, sleeping roughly
2, 4, 8, 16, 32, 64, 128 seconds (plus jitter) between attempts.

### Search is only as good as Reddit's search

`search_reddit` uses Reddit's own search engine — RSS is just the output format,
so results are identical to the website/API search, not a separate (weaker)
index. That engine has real limits:

- **It doesn't search comment text** — only post titles and bodies (and
  community names). A term that only appears in a comment won't be found.
- **Very new posts lag** — search indexing isn't instant. To catch brand-new
  posts reliably, use `browse_subreddit(sort="new")` instead of search.
- **It isn't exhaustive** — low-relevance results get dropped or buried.

So a "no results" means *"Reddit's search didn't surface it,"* not a guarantee
it was never posted anywhere on the site.
