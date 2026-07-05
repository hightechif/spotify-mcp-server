## MODIFIED Requirements

### Requirement: Spotify Client Configuration
The system SHALL load Spotify client credentials (Client ID, Client Secret, and Refresh Token) from environment variables or a `.env` file located in the script's directory. It SHALL support resolving the project directory via system environment variables to support running the server without hardcoding absolute paths.

#### Scenario: Load valid credentials
- **WHEN** the server starts with valid environment variables
- **THEN** it SHALL successfully initialize the Spotify client and fetch an initial access token

#### Scenario: Load credentials from relative .env file
- **WHEN** the server is executed from any working directory
- **THEN** it SHALL resolve and load the `.env` file from the directory where the script files reside
