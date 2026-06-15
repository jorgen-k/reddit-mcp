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

1. **Bump the version in two files (keep them identical):**
   - `pyproject.toml` → `version`
   - `server.json` → top-level `version`

   Update `CHANGELOG.md`. (The workflow fails fast if the tag, `pyproject.toml`,
   and `server.json` versions disagree.)

2. **Commit, tag, push:**
   ```sh
   git commit -am "release: X.Y.Z"
   git tag -a vX.Y.Z -m "reddit-mcp X.Y.Z"
   git push origin main --follow-tags
   ```

3. **Watch the run** under the repo's Actions tab. On success:
   ```sh
   curl "https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.jorgen-k/reddit-mcp"
   ```

## Notes

- The workflow also packs the Claude Desktop extension from `extension/manifest.json`
  and attaches `reddit-rss-mcp.mcpb` to the GitHub release. The manifest version is
  set from the tag automatically, so it does not need a manual bump. The README's
  one-click link points at `releases/latest/download/reddit-rss-mcp.mcpb`.
- Ownership verification: the registry checks that the PyPI description (this
  repo's README) contains `<!-- mcp-name: io.github.jorgen-k/reddit-mcp -->`.
  Do not remove that marker.
- Manual fallback (if you ever need to publish from a laptop) is `uv build &&
  uv publish --token <pypi-token>` followed by `mcp-publisher login github &&
  mcp-publisher publish`.
