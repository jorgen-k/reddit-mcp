# reddit-mcp

<!-- mcp-name: io.github.jorgen-k/reddit-mcp -->

**Read Reddit from Claude without an API key.** No app registration, no account.

Reddit's data API is effectively closed. New apps need a stated moderation use
case and manual approval, anonymous `.json` access is blocked, and the free tier
that third-party tools were built on is gone. Most "Reddit for LLMs" integrations
now start with a credentials dance you can't complete.

Reddit still publishes public Atom/RSS feeds for every subreddit, thread, user and
search. This is a small local MCP server that reads those feeds and hands Claude
the fields that matter: browse a subreddit, read a thread and its comments, search
across the site.

Those feeds are published to be fetched, which is why this keeps working. It reads a
supported path in a format frozen since 2005, so there is no markup to break when
Reddit ships its next redesign.

**What you don't get:** scores, upvote ratios, comment counts. Those exist only in
the gated API, and nothing here fakes them. Titles, authors, timestamps, and the
full text of posts and comments all come through.

## Install

`reddit-rss-mcp` is on PyPI (the plain `reddit-mcp` name belongs to an unrelated
project). You need [`uv`](https://docs.astral.sh/uv/) on your machine; it handles
Python and dependencies itself, and there is nothing else to set up.

**Claude Code:**

```sh
claude mcp add reddit -s user -- uvx reddit-rss-mcp
```

Verify with `claude mcp list` (should show `reddit: ✓ Connected`). If Claude can't
find `uvx`, use its absolute path (`which uvx`) instead of the bare command.

**Claude Desktop, one click:** download `reddit-rss-mcp.mcpb` from the
[latest release](https://github.com/jorgen-k/reddit-mcp/releases/latest) and drag it
into **Settings → Extensions**. No JSON editing, no absolute paths. (It runs
`uvx reddit-rss-mcp`, so `uv` still needs to be on your PATH.)

**Claude Desktop & Cowork, manual config:** add this to
`~/Library/Application Support/Claude/claude_desktop_config.json`, using the
absolute path from `which uvx` (the app doesn't inherit your shell `PATH`):

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

If the file already has other top-level keys, add `mcpServers` alongside them
rather than overwriting the file. Then:

1. **Fully quit the app** (`Cmd+Q`, not just closing the window). The running app
   rewrites this file, so an edit made while it's open can be discarded.
2. **Relaunch.** It may take a couple of restarts before the server registers.
3. **Grant permission** when the app prompts to run the server.

> **Don't use a Custom Connector** (the "add server by URL" option) for a local
> server. Those are dialed from Anthropic's cloud and can't reach `localhost`, no
> matter the cert or tunnel. The config-file method above spawns the server on your
> own machine, which is what works.

## Tools

| Tool | What it does |
|------|--------------|
| `search_reddit(query, subreddit=None, sort="relevance", time_filter="all", limit=25)` | Search Reddit discussions for real user opinions and experiences on a topic. |
| `browse_subreddit(subreddit, sort="hot", time_filter="day", limit=25)` | What a community is posting right now (`hot`/`new`/`top`/`rising`/`controversial`). |
| `get_post(url, comment_limit=50)` | One thread in full: the post plus its comments (a flat list; the reply tree isn't in the feed). |
| `fetch_json(url)` | The remaining Reddit feed shapes: `/user/<name>`, multireddits, `/domain/<site>`. |

`fetch_json` is deliberately not a general web fetcher. URLs on other hosts are
refused unless you start the server with `REDDIT_MCP_ALLOW_ANY_URL=1`, so an
unrelated fetch tool doesn't sit in Claude's tool list waiting to be picked at the
wrong moment.

## Other ways to install

### From GitHub (latest `main`, no clone)

To run unreleased changes, point `uvx` at the repo and the `reddit-rss-mcp` entry
point. Append `@v1.1.2` (or any tag) to pin a release instead of tracking `main`:

```sh
claude mcp add reddit -s user -- uvx --from git+https://github.com/jorgen-k/reddit-mcp reddit-rss-mcp
```

### From a local clone

Prefer this if you want to edit the code:

```sh
git clone https://github.com/jorgen-k/reddit-mcp.git
cd reddit-mcp
claude mcp add reddit -s user -- uv --directory "$(pwd)" run server.py
```

For Claude Desktop & Cowork, the same config file as above, with absolute paths
from `which uv` and `pwd`:

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

### Updating after a code change

The server is a long-lived process, spawned once when the client connects. Editing
`server.py` does not hot-reload it; the running process keeps the old code until
it's restarted.

- **Claude Code:** run `/mcp`, select `reddit`, and reconnect it (or restart Claude
  Code).
- **Claude Desktop & Cowork:** fully quit the app (`Cmd+Q`) and relaunch.

## Limits worth knowing

Read-only, public content only. Be considerate with request volume; these are
public feeds.

**No scores, vote counts, or comment counts.** RSS doesn't carry them. For those
you need Reddit's Data API, which now requires a moderation use case and approval.

**Rate limiting.** Reddit throttles unauthenticated RSS aggressively. On an HTTP
429 the server retries with backoff, honoring the `Retry-After` header when present
and otherwise sleeping roughly 2, 4, 8, 16, 32, 64, 128 seconds (plus jitter) across
up to 7 retries. It also keeps a minimum gap between outbound requests to avoid
tripping the limit in the first place. All tools share this.

**Search is only as good as Reddit's search.** `search_reddit` uses Reddit's own
search engine; RSS is just the output format, so results match the website, not a
separate weaker index. That engine has real limits:

- **It doesn't search comment text**, only post titles and bodies (and community
  names). A term that appears only in a comment won't be found.
- **Very new posts lag**, because indexing isn't instant. To catch brand-new posts
  reliably, use `browse_subreddit(sort="new")`.
- **It isn't exhaustive.** Low-relevance results get dropped or buried.

So "no results" means Reddit's search didn't surface it, not that it was never
posted.

## License

MIT. See [LICENSE](LICENSE).
