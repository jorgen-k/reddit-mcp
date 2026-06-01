# reddit-mcp (Cowork plugin)

Adds Reddit-reading tools to Claude via Reddit's public RSS feeds — **no
account, app, or API key**.

This plugin bundles a local stdio MCP server (`server.py`) and runs it on your
device. Custom Connectors are dialed from Anthropic's cloud and can't reach a
local server, so a plugin (run locally) is the supported way to use a local MCP
server in Cowork.

## Requirements

- [`uv`](https://docs.astral.sh/uv/) must be installed and on your `PATH`. On
  first run it provisions an isolated Python environment automatically.

If Cowork can't find `uv`, edit `.mcp.json` and replace `"uv"` with its absolute
path (find it with `which uv`).

## Tools

| Tool | What it does |
|------|--------------|
| `browse_subreddit` | Posts from a subreddit (`hot`/`new`/`top`/`rising`/`controversial`). |
| `get_post` | A post plus its comments. |
| `search_reddit` | Search Reddit, optionally scoped to one subreddit. |
| `fetch_json` | Any Reddit URL (→ RSS) or other JSON endpoint. |

## Notes

- Read-only, public content only.
- RSS doesn't include scores, upvote ratios, or comment counts.

Source & the standalone (Claude Code) version: <https://github.com/jorgen-k/reddit-mcp>
