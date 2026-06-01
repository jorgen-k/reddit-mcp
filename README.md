# reddit-mcp

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

Clone it somewhere first:

```sh
git clone https://github.com/jorgen-k/reddit-mcp.git
cd reddit-mcp
```

### Claude Code

```sh
claude mcp add reddit -s user -- uv --directory "$(pwd)" run server.py
```

Verify with `claude mcp list` (should show `reddit: ✓ Connected`). If Claude
can't find `uv`, use its absolute path (`which uv`) instead of bare `uv`.

### Claude Desktop

Add this under the top-level `"mcpServers"` key in your
`claude_desktop_config.json` (macOS:
`~/Library/Application Support/Claude/`). Use **absolute paths** — Desktop
doesn't inherit your shell `PATH`, so run `which uv` and `pwd` and paste the
results in:

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

Restart Claude Desktop to load it.

### Cowork (remote / HTTP transport)

Cowork doesn't load hand-edited `mcpServers` config and may run agents in a
sandboxed VM, so it expects a connector reached over a **URL**. Run the server
in HTTP mode and add it as a custom connector.

1. Start the server (keep it running — unlike stdio, it isn't auto-spawned):
   ```sh
   uv run server.py --http
   ```
   It listens at `http://127.0.0.1:9090/mcp`. Override with `REDDIT_MCP_HOST`
   / `REDDIT_MCP_PORT`.
2. In Cowork, add a custom MCP connector pointing at that URL.

> **If Cowork can't reach `127.0.0.1`** (its sandbox has its own localhost),
> bind to all interfaces and use your machine's IP instead:
> ```sh
> REDDIT_MCP_HOST=0.0.0.0 uv run server.py --http
> ```
> then point Cowork at `http://<your-host-ip>:9090/mcp`.

The same HTTP endpoint also works for Claude Code:
```sh
claude mcp add reddit-http --transport http http://127.0.0.1:9090/mcp
```

## Notes

- Read-only, public content only.
- No scores/vote counts/comment counts (RSS limitation). For those you'd need
  Reddit's Data API, which now requires a moderation use case + approval.
- Be considerate with request volume — these are public feeds.
