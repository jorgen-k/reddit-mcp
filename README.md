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

### Cowork (install the plugin)

Cowork's **Custom Connectors are dialed from Anthropic's cloud**, so a
`localhost` URL can never reach a server on your machine — no tunnel or cert
fixes that. The supported way to run a *local* MCP server in Cowork is a
**plugin** that runs on-device.

Install the prebuilt plugin:

1. Grab **`reddit-mcp.plugin`** from this repo (it bundles the stdio server).
2. Open it with Cowork / install it from Cowork's plugins UI and accept it.

`uv` must be installed and on your `PATH`. If Cowork can't find it, edit the
plugin's `.mcp.json` and replace `"uv"` with the absolute path from `which uv`.

> The plugin source lives in [`plugin/reddit-mcp/`](plugin/reddit-mcp/). Rebuild
> the `.plugin` with:
> ```sh
> cd plugin/reddit-mcp && zip -rq ../../reddit-mcp.plugin . \
>   -x ".venv/*" "__pycache__/*" "*.pyc" "uv.lock"
> ```

### Remote / hosted (optional)

The server can also run over streamable-HTTP for a *publicly hosted* deployment
(a Custom Connector can reach a real `https://` URL, just not `localhost`):

```sh
uv run server.py --http        # http://127.0.0.1:9090/mcp
```

Set `REDDIT_MCP_HOST` / `REDDIT_MCP_PORT` to change the bind address, and
`REDDIT_MCP_CERTFILE` / `REDDIT_MCP_KEYFILE` to serve HTTPS directly. This is
only useful if you expose it on a public host with a real certificate; for local
use, prefer the plugin (Cowork) or stdio (Claude Code) above.

## Notes

- Read-only, public content only.
- No scores/vote counts/comment counts (RSS limitation). For those you'd need
  Reddit's Data API, which now requires a moderation use case + approval.
- Be considerate with request volume — these are public feeds.
