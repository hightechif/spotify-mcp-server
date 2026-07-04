## 1. Project Setup & Environment Configuration

- [x] 1.1 Create project directory structure and files
- [x] 1.2 Initialize project using `uv init` and add dependencies (mcp, httpx, python-dotenv, mypy)
- [x] 1.3 Create .gitignore, pyproject.toml, and .env.example templates
- [x] 1.4 Implement one-time OAuth token retriever script (get_token.py)

## 2. Core Spotify Client & Authentication

- [x] 2.1 Implement Spotify Auth module (spotify_auth.py) to manage access and refresh tokens
- [x] 2.2 Implement request client with auto-refresh mechanism for expired access tokens

## 3. MCP Server Core, Resource, and Prompts

- [x] 3.1 Initialize MCP server and connect basic lifecycle methods
- [x] 3.2 Implement resource `spotify://status` returning metadata of currently playing track
- [x] 3.3 Implement prompt `vibe_check` providing structure for music curation conversations

## 4. Playback Control Tools

- [x] 4.1 Implement device manager to detect active devices and target the web player
- [x] 4.2 Implement `get_current_playback` tool
- [x] 4.3 Implement standard playback control tools (pause, resume, skip next/prev, set volume, add to queue)

## 5. Music Discovery & Playback Trigger Tools

- [x] 5.1 Implement `search_spotify` tool
- [x] 5.2 Implement `play_by_search` tool targeting active browser/web player
- [x] 5.3 Implement `get_recommendations` tool

## 6. Manual Verification & Error Handling

- [x] 6.1 Add defensive error handling for "Player Not Found" (HTTP 404) with helpful user prompts
- [x] 6.2 Run static analysis and strict type checking using mypy (`uv run mypy .`)
- [x] 6.3 Validate that the MCP server runs correctly and tools are fully registered in the client
