# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
