# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-09-03

### Added

- Support for any MCP-compatible client including Codex

## [1.1.5] - 2026-09-03

### Fixed

- `search_reddit` returned subreddit matches alongside posts. Reddit's search
  feed mixes `t5` (subreddit) entries in with `t3` (post) entries, and those
  arrived with a null author, subreddit and timestamp, and the community's
  sidebar blurb as their text. They also counted against `limit`, so a search
  for six results could return four posts and two subreddits. Results are now
  filtered to posts, and the feed is asked for a few extra entries so `limit`
  posts still come back. Thanks to @volkanncicek (#4).

## [1.1.4]

### Changed

- Migrated to MCP Python SDK 2.x. `FastMCP` was renamed to `MCPServer`, so
  `server.py` now imports `MCPServer` from `mcp.server.mcpserver`. The tool
  decorator and stdio transport are unchanged, so client configuration and the
  four tools behave exactly as before.

### Fixed

- Dependencies are now pinned below the next major (`mcp>=2.1,<3`,
  `httpx>=0.27,<1`) instead of tracking the latest release. The unbounded
  `mcp>=1.2.0` in 1.1.2 silently resolved to the 2.x SDK, which this server
  could not import; 1.1.3 capped it at `<2` as an emergency fix and this
  release moves forward properly.

## [1.1.3]

### Fixed

- `fetch_json` accepted URLs on any host, which was never the intent. It now
  covers the Reddit feed shapes the other tools don't (`/user/<name>`,
  multireddits, `/domain/<site>`) and refuses other hosts unless
  `REDDIT_MCP_ALLOW_ANY_URL=1` is set. The three Reddit tools are unaffected.
- Pinned `mcp<2`. The MCP Python SDK 2.x renamed `FastMCP` to `MCPServer`, so the
  unbounded `mcp>=1.2.0` in 1.1.2 resolves to a version this server cannot import.
  A fresh install of 1.1.2 fails at startup with `ModuleNotFoundError: No module
  named 'mcp.server.fastmcp'`.

## [1.1.2] - 2026-06-15

### Added

- One-click Claude Desktop install: a `.mcpb` extension (runs `uvx reddit-rss-mcp`)
  is built and attached to each GitHub release.

### Fixed

- Shortened the `server.json` description to <=100 characters so the MCP Registry
  publish succeeds (1.1.1 published to PyPI but was rejected by the registry).

## [1.1.1] - 2026-06-15

First published release. No functional code changes from 1.1.0.

### Added

- Published to PyPI as [`reddit-rss-mcp`](https://pypi.org/project/reddit-rss-mcp/)
  and listed in the official MCP Registry as `io.github.jorgen-k/reddit-mcp`.
- Automated release workflow: pushing a `v*` tag publishes to PyPI (trusted
  publishing) and the MCP Registry via GitHub OIDC, with no stored secrets.

## [1.1.0] - 2026-06-15

### Added

- Transparent retry with backoff on Reddit HTTP 429 rate limits. The `Retry-After`
  header is honored when present; otherwise the request uses exponential backoff
  with jitter (up to 7 retries). A global minimum interval between outbound
  requests reduces 429s at the source. Shared across all tools (`browse_subreddit`,
  `get_post`, `search_reddit`, `fetch_json`). Closes #1.
- Unit tests for the retry/backoff and throttle layer.

### Fixed

- `browse_subreddit` params dict type annotation (`str` was not assignable to the
  inferred `int`-only dict).

## [1.0.0] - 2026-06-01

### Added

- Initial stdio MCP server fetching and refining Reddit content via public
  RSS/Atom feeds: `browse_subreddit`, `get_post`, `search_reddit`, and a generic
  `fetch_json`. No authentication required.
