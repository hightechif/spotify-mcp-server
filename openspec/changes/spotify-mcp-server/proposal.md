## Why

We want to control Spotify playback and search tracks/playlists directly from an AI client (such as Claude or Antigravity IDE) using the Model Context Protocol (MCP). Building a custom Python-based MCP server for the Spotify Web API will make the AI context-aware of our listening environment and allow it to act as an automated DJ or developer companion.

## What Changes

- Create a new Python project structure for a custom Model Context Protocol (MCP) server.
- Integrate the Spotify Web API for media playback control, search, and recommendation features.
- Implement Option A (Refresh Token) authentication using OAuth 2.0. The server will read `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, and `SPOTIFY_REFRESH_TOKEN` from environment variables (or `.env` file) and handle access token refresh automatically.
- Provide MCP Tools:
  - `get_current_playback`: Returns details of active playing track, artist, progress, volume, and playback state.
  - `pause_playback` / `resume_playback`: Pause or resume Spotify.
  - `skip_next` / `skip_previous`: Go to next or previous track.
  - `set_volume`: Set player volume (0-100).
  - `search_spotify`: Search tracks, albums, artists, or playlists.
  - `play_by_search`: Find the top matching search result and play it immediately.
  - `get_recommendations`: Fetch recommended tracks based on seed genres.
  - `add_to_queue`: Queue a specific track URI.
- Focus the target playback device to the user's active Web Player/current web browser.
- Expose a dynamic resource `spotify://status` reflecting current track details.
- Provide a prompt template `vibe_check` to guide musical context interactions.

## Capabilities

### New Capabilities
- `spotify-mcp-tools`: A Python-based MCP server providing playback control, search, recommendations, and status resources for the Spotify Web API.

### Modified Capabilities

## Impact

- **External APIs**: Spotify Web API (requires a registered developer app).
- **Dependencies & Toolchain**: `uv` (project and package manager), `mcp` Python SDK, `httpx` (async HTTP client), `python-dotenv` for configuration, and `mypy` for static type checking.
- **Client Configuration**: Updates to Claude / IDE settings to include the new Python server command (e.g., using `uv run`).
