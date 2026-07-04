## Context

We want to build a custom Python-based Model Context Protocol (MCP) server that interfaces with the Spotify Web API. It allows an AI assistant (running locally or inside an IDE) to control music playback, search for tracks/playlists, adjust volume, queue tracks, get recommended music, and read current playback status.

## Goals / Non-Goals

**Goals:**
- Implement single-user authentication using a pre-authorized Client ID, Client Secret, and Refresh Token (Option A) stored in `.env`.
- Build a Python script that implements the MCP server protocol using the official `mcp` SDK.
- Expose a set of playback control tools: pause, resume, skip, set volume, queue.
- Expose search tools (`search_spotify`, `play_by_search`) and metadata discovery tools (`get_recommendations`).
- Implement automatic access token refreshing using the Spotify Accounts service.
- Prioritize targeting the active web browser session (Web Player) or the active device.
- Expose the currently playing track status as an MCP resource (`spotify://status`).
- Define the `vibe_check` MCP prompt template for context-rich music recommendations.

**Non-Goals:**
- Building a full user interface (the user uses the standard Spotify app/web player and their AI client interface).
- Implementing multi-user dynamic OAuth registration inside the MCP server process.
- Developing a custom audio player engine (relies completely on the official Spotify player APIs).

## Decisions

### Decision 1: Tech Stack & Libraries
- **Choice**: Python managed by `uv` (project and package management), using the official `mcp` Python SDK, `httpx` (async HTTP client), and `python-dotenv` for configuration. Static typing and strict type checking SHALL be enforced across all codebase files using `mypy`.
- **Rationale**: Python allows for fast development and meets the user's explicit request. Using `httpx` allows us to write non-blocking async code. `uv` ensures reproducible, modern, and fast environment/package management, and `mypy` guarantees type safety and reduces runtime bugs by enforcing strict static type annotations on all code signatures.


### Decision 2: Single-User Authentication (Option A)
- **Choice**: Storing a static `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, and `SPOTIFY_REFRESH_TOKEN` in a `.env` file.
- **Rationale**: Building a dynamic OAuth flow with redirects inside the MCP server is complex, security-sensitive, and unnecessary for a personal single-user server. We will provide a simple companion script (`get_token.py`) that the developer runs once to generate the initial refresh token.
- **Alternatives**: Dynamic OAuth server. Adds too much overhead and code complexity.

### Decision 3: Device Targeting (Browser Focus)
- **Choice**: Automatically query the user's active Spotify devices. Target the device identified as a web browser ("Web Player" or Type: "Computer"). If not explicitly found, fallback to the currently active device. If no device is active, return a descriptive message.
- **Rationale**: Commands like "play" or "set volume" fail if no device is selected. Rather than prompting the user for a device ID on every turn, the server will intelligently locate and target the active browser/computer session.
- **Alternatives**: Requiring a hardcoded device ID in config, which is fragile since device IDs change across sessions.

## Risks / Trade-offs

- **[Risk]** Spotify requires an active session to control. If Spotify is closed or idle, commands return HTTP 404 (Player not found).
  - *Mitigation*: The MCP tools will intercept 404 player errors and return a clear, user-friendly prompt: `"Spotify is currently inactive. Please open open.spotify.com in your web browser or open the Spotify app, play a song, and try again."`
- **[Risk]** Spotify token expiry (1 hour).
  - *Mitigation*: The server will check token age/expiry before every API request, automatically requesting a new access token from the refresh token endpoint if needed.
