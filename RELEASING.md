# Releasing

Releases are automated by `.github/workflows/publish.yml`. Pushing a `v*` tag
builds the package and publishes it to:

1. **PyPI** as [`reddit-rss-mcp`](https://pypi.org/project/reddit-rss-mcp/) — via
   trusted publishing (OIDC), no token.
2. The **official MCP Registry** as `io.github.jorgen-k/reddit-mcp` (metadata only,
   pointing at the PyPI package) — via `mcp-publisher login github-oidc`, no token.

No secrets are stored anywhere; both steps authenticate through GitHub OIDC.

## One-time setup (PyPI trusted publisher)

Before the first release, register this repo as a trusted publisher on PyPI. You
can do this even though the project doesn't exist yet (PyPI calls it a "pending
publisher"); the first CI run creates the project.

Go to https://pypi.org/manage/account/publishing/ and add a GitHub publisher:

| Field | Value |
| --- | --- |
| PyPI Project Name | `reddit-rss-mcp` |
| Owner | `jorgen-k` |
| Repository name | `reddit-mcp` |
| Workflow name | `publish.yml` |
| Environment name | *(leave blank)* |

That's it. No API token is needed, so you can delete any account token you
created earlier.

## Each release

The tag is the only place the version is written by hand. The workflow injects it
into `pyproject.toml`, `server.json` (both the top-level field and
`packages[0].version`) and `extension/manifest.json` at build time, so there is
nothing to bump and nothing to keep in sync.

1. **Write the `CHANGELOG.md` section** for the new version, heading
   `## [X.Y.Z] - YYYY-MM-DD`. It becomes the GitHub release notes verbatim, so
   an empty or missing section shows up there.

2. **Commit, tag, push:**
   ```sh
   git commit -am "docs: changelog for X.Y.Z"
   git tag -a vX.Y.Z -m "reddit-mcp X.Y.Z"
   git push origin main --follow-tags
   ```

3. **Watch the run** under the repo's Actions tab. On success:
   ```sh
   curl "https://registry.modelcontextprotocol.io/v0/servers?search=io.github.jorgen-k/reddit-mcp"
   ```

The committed version fields are therefore expected to lag behind the latest
release. That is deliberate: the tag is the source of truth. Do not "fix" them.

The tag pattern is `v[0-9]+.[0-9]+.[0-9]+`, so a stray tag like `vNext` no longer
triggers a publish.

## Notes

- The workflow also packs the Claude Desktop extension from `extension/manifest.json`
  and attaches `reddit-rss-mcp.mcpb` to the GitHub release. The README's one-click
  link points at `releases/latest/download/reddit-rss-mcp.mcpb`.
- `.github/workflows/test.yml` runs the tests on every push and PR, and weekly on
  a schedule. Because `uv.lock` is gitignored, every run resolves dependencies
  fresh, so the weekly run is what catches a breaking upstream release before it
  reaches a release attempt.
- `.github/dependabot.yml` raises the dependency caps in `pyproject.toml` and the
  action versions in the workflows, weekly. Keep the caps: an unbounded
  `mcp>=1.2.0` is how the 2.x SDK silently broke 1.1.2 for every fresh install.
- Ownership verification: the registry checks that the PyPI description (this
  repo's README) contains `<!-- mcp-name: io.github.jorgen-k/reddit-mcp -->`.
  Do not remove that marker.
- Manual fallback (if you ever need to publish from a laptop) is `uv build &&
  uv publish --token <pypi-token>` followed by `mcp-publisher login github &&
  mcp-publisher publish`.
