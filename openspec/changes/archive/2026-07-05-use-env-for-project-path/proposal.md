## Why

The current installation and setup documentation (README.md) hardcodes the personal absolute path of the user's workspace in the Claude Desktop configuration block. Sharing the repository exposes personal path details to the public. Additionally, the python scripts look for the `.env` file in the current working directory, which prevents executing the server from other directories unless explicitly changed.

## What Changes

- Modify `README.md` to reference a generic environment variable (`SPOTIFY_MCP_DIR` or `SPOTIFY_MCP_PATH`) instead of the user's hardcoded absolute path `/Users/ridhanfadhilah/Public/Fadhil/AI/mcp/spotify-mcp-server`.
- Provide clear instructions in `README.md` on how to set the environment variable and configure Claude Desktop using shell command runner (e.g. `zsh` or `bash`) to expand the environment variable.
- Update `spotify_auth.py` and `get_token.py` to search for and load the `.env` file using a path relative to the script file, enabling execution from any directory.

## Capabilities

### New Capabilities
<!-- Capabilities being introduced. Replace <name> with kebab-case identifier (e.g., user-auth, data-export, api-rate-limiting). Each creates specs/<name>/spec.md -->

### Modified Capabilities
<!-- Existing capabilities whose REQUIREMENTS are changing (not just implementation).
     Only list here if spec-level behavior changes. Each needs a delta spec file.
     Use existing spec names from openspec/specs/. Leave empty if no requirement changes. -->
- `spotify-mcp-tools`: Modify Spotify Client Configuration requirement to specify loading .env relative to the script directory, and reference environment-variable-based path configuration for integration.

## Impact

- `README.md`: Update setup documentation.
- `spotify_auth.py`: Modify `.env` load logic to be relative to the script's directory.
- `get_token.py`: Modify `.env` load logic to be relative to the script's directory.
