# Spotify MCP Server

A Python-based Model Context Protocol (MCP) server that connects your AI assistant (Claude Desktop, Cursor, etc.) directly to the Spotify Web API. This allows the AI to inspect your current playback state, search for music, trigger recommendations, and control your player (play, pause, skip, adjust volume, queue tracks).

Built using **Python 3.12+**, the official **FastMCP SDK**, **`uv`** for dependency/project management, and fully type-annotated with strict **`mypy`** validation.

---

## Features

### 🛠️ Exposed Tools
* **`get_current_playback`**: Retrieves details about your active device, current volume, track name, artist, album, and progress.
* **`pause_playback` / `resume_playback`**: Pauses or resumes playback.
* **`skip_next` / `skip_previous`**: Skips to the next or previous track.
* **`set_volume`**: Adjusts player volume (0 to 100).
* **`add_to_queue`**: Appends a specific track URI to the queue.
* **`search_spotify`**: Searches for tracks, albums, artists, or playlists.
* **`play_by_search`**: Searches for an item and immediately starts playing the top result.
* **`get_recommendations`**: Fetches track recommendations based on seed genres (e.g. `lofi,chill`).

### 📊 Exposed Resources
* **`spotify://status`**: Exposes the text description of the currently playing track.

### 💬 Exposed Prompts
* **`vibe_check`**: Guides the AI to curate and play a playlist matching your current coding task, energy level, and mood.

---

## Prerequisites

1. **Spotify Premium**: The Spotify Web API Player endpoints require a Spotify Premium subscription to accept control commands.
2. **`uv` Package Manager**: Install `uv` if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

---

## Setup & Installation

### 1. Register a Spotify Developer App
1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and log in.
2. Click **Create App** and fill in the details:
   - **App name**: E.g. `My Local MCP Server`
   - **Redirect URI**: `http://127.0.0.1:8888/callback` (Crucial for the authentication script to run successfully)
3. Under the app settings, copy your **Client ID** and **Client Secret**.

### 2. Configure Environment Secrets
Create a `.env` file in the root of this project:
```bash
cp .env.example .env
```
Open `.env` and fill in your client keys:
```ini
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_REDIRECT_PORT=8888
```

### 3. Generate Spotify Refresh Token
Run the built-in OAuth helper script:
```bash
uv run get_token.py
```
* This script spins up a temporary web server on `127.0.0.1:8888` and opens your default web browser to authorize the required permissions (`user-read-playback-state`, `user-modify-playback-state`, `user-read-currently-playing`).
* After clicking "Agree", you will see a success message. Return to the terminal and copy the printed `SPOTIFY_REFRESH_TOKEN` to your `.env` file:
```ini
SPOTIFY_REFRESH_TOKEN=your_generated_refresh_token_here
```

---

## Development & Type Checking

Ensure the codebase is type-safe and conforms to the static analysis rules:
```bash
uv run mypy .
```

---

## MCP Client Configuration

To register this server with your AI client, add the following configuration block:

### Claude Desktop
Add this to your `claude_desktop_config.json` (usually located at `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "spotify": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/ridhanfadhilah/Public/Fadhil/AI/mcp/spotify-mcp-server",
        "run",
        "main.py"
      ]
    }
  }
}
```

*Note: Replace `/Users/ridhanfadhilah/Public/Fadhil/AI/mcp/spotify-mcp-server` with the absolute path of this workspace if it is located elsewhere.*
