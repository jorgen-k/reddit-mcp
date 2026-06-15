# Releasing

This project is published in two places, in order:

1. **PyPI** as [`reddit-rss-mcp`](https://pypi.org/project/reddit-rss-mcp/) (the
   actual installable artifact).
2. The **official MCP Registry** as `io.github.jorgen-k/reddit-mcp` (metadata only,
   pointing at the PyPI package).

The registry hosts only metadata, so PyPI must be published first.

## One-time setup

- A **PyPI account** with an API token (https://pypi.org/manage/account/token/).
- A **GitHub account** (used to authenticate to the registry; the server name must
  live under `io.github.<your-username>/`, which is why it is `io.github.jorgen-k/...`).
- The **`mcp-publisher`** CLI:
  ```sh
  brew install mcp-publisher
  # or, without Homebrew:
  curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_$(uname -s | tr '[:upper:]' '[:lower:]')_$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/').tar.gz" | tar xz mcp-publisher && sudo mv mcp-publisher /usr/local/bin/
  ```

## Each release

1. **Bump the version in two files and keep them identical:**
   - `pyproject.toml` → `version`
   - `server.json` → top-level `version` **and** `packages[0].version`

   Update `CHANGELOG.md` and tag the commit (`git tag -a vX.Y.Z -m "reddit-mcp X.Y.Z"`).

2. **Build and publish to PyPI:**
   ```sh
   rm -rf dist && uv build
   uv publish            # prompts for the token, or set UV_PUBLISH_TOKEN
   ```
   Ownership verification: the registry checks that the PyPI description (this
   repo's README) contains `<!-- mcp-name: io.github.jorgen-k/reddit-mcp -->`.
   Do not remove that marker.

3. **Publish metadata to the MCP Registry:**
   ```sh
   mcp-publisher login github     # device-code flow in the browser
   mcp-publisher publish          # reads ./server.json
   ```

4. **Verify:**
   ```sh
   curl "https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.jorgen-k/reddit-mcp"
   ```

## Notes

- The `mcp-publisher` login is interactive (GitHub device code), so this is a
  manual step; it cannot be fully automated from here.
- To automate later, the registry supports publishing from GitHub Actions
  (OIDC-based auth) instead of the device-code flow.
