# spotify-mcp-tools Specification

## Purpose
TBD - created by archiving change spotify-mcp-server. Update Purpose after archive.
## Requirements
### Requirement: Spotify Client Configuration
The system SHALL load Spotify client credentials (Client ID, Client Secret, and Refresh Token) from environment variables or a `.env` file located in the script's directory. It SHALL support resolving the project directory via system environment variables to support running the server without hardcoding absolute paths.

#### Scenario: Load valid credentials
- **WHEN** the server starts with valid environment variables
- **THEN** it SHALL successfully initialize the Spotify client and fetch an initial access token

#### Scenario: Load credentials from relative .env file
- **WHEN** the server is executed from any working directory
- **THEN** it SHALL resolve and load the `.env` file from the directory where the script files reside

### Requirement: Spotify Access Token Refresh
The system SHALL automatically refresh the Spotify access token using the refresh token before it expires or if a request fails with an expired token error (HTTP 401).

#### Scenario: Auto-refresh on request
- **WHEN** an API request is made with an expired access token
- **THEN** the system SHALL fetch a new access token and retry the original request

### Requirement: Playback State Retrieval
The system SHALL provide an MCP tool `get_current_playback` to fetch active playback information (track, artist, state, progress, volume).

#### Scenario: Get active playback
- **WHEN** the `get_current_playback` tool is called
- **THEN** it SHALL query Spotify and return the player details

### Requirement: Playback Control
The system SHALL provide MCP tools `pause_playback`, `resume_playback`, `skip_next`, `skip_previous`, `set_volume`, and `add_to_queue`.

#### Scenario: Control command execution
- **WHEN** any playback control tool is called
- **THEN** it SHALL send the corresponding command to the Spotify player API

### Requirement: Music Search
The system SHALL provide an MCP tool `search_spotify` to find tracks, albums, artists, or playlists by query.

#### Scenario: Search query execution
- **WHEN** `search_spotify` is called with a query
- **THEN** it SHALL return a list of matching items from Spotify

### Requirement: Play By Search
The system SHALL provide an MCP tool `play_by_search` that searches for a track or playlist and plays the top match.

#### Scenario: Play top match
- **WHEN** `play_by_search` is called
- **THEN** it SHALL search Spotify and trigger playback of the top matching item on the active web browser player

### Requirement: Track Recommendations
The system SHALL provide an MCP tool `get_recommendations` to fetch recommended tracks.

#### Scenario: Get recommendations
- **WHEN** `get_recommendations` is called with seed genres
- **THEN** it SHALL return a list of recommended tracks from Spotify

### Requirement: Target Web Browser Player
The system SHALL identify and target the active Spotify Web Player (web browser) session for playback controls.

#### Scenario: Target web player device
- **WHEN** a playback command is sent
- **THEN** it SHALL attempt to direct the request to the active Spotify Web Player device ID

### Requirement: Track Status Resource
The system SHALL expose an MCP resource `spotify://status` reflecting the currently playing track metadata.

#### Scenario: Read track status
- **WHEN** the resource `spotify://status` is requested
- **THEN** it SHALL return the text description of the currently playing track

### Requirement: Vibe Check Prompt
The system SHALL define an MCP prompt template `vibe_check` to guide custom playlist generation.

#### Scenario: Retrieve vibe check prompt
- **WHEN** the `vibe_check` prompt is requested
- **THEN** it SHALL return the structured prompt instructions

### Requirement: Static Type Annotation Verification
The codebase SHALL be fully type-annotated, and type validation MUST be verified with static code analysis.

#### Scenario: Running type checks
- **WHEN** type checking tools are run on the codebase
- **THEN** they SHALL successfully pass without any typing errors or warnings

