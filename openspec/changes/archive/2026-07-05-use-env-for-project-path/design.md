## Context

The workspace path `/Users/ridhanfadhilah/Public/Fadhil/AI/mcp/spotify-mcp-server` is currently hardcoded in the setup documentation (`README.md`). If the workspace/configuration is shared, this exposes the user's personal file system structure. Additionally, running the Python scripts via a client requires them to run in the script's directory because `.env` files are loaded relative to the current working directory.

## Goals / Non-Goals

**Goals:**
- Hide the hardcoded absolute directory path in checked-in documentation.
- Enable running the Spotify MCP server from any working directory by resolving `.env` relative to the script file path.
- Support configuring the absolute path via environment variables in the client configuration.

**Non-Goals:**
- Change the Spotify API authentication logic or endpoints.
- Support non-POSIX shell environments (focus is on macOS/Unix).

## Decisions

### 1. Configure Client to Run in Shell with Environment Variables
Instead of referencing the absolute path directly in client configurations (such as `claude_desktop_config.json`), we will document how to run the server via a login shell (`zsh -l` or `bash -l`). This allows the shell to expand system environment variables.
- The user exports `SPOTIFY_MCP_DIR` in their shell profile (e.g. `~/.zshrc`).
- The client is configured to run:
  ```json
  "command": "zsh",
  "args": ["-l", "-c", "uv --directory \"$SPOTIFY_MCP_DIR\" run main.py"]
  ```

### 2. Relative .env File Loading in Scripts
Modify both `spotify_auth.py` and `get_token.py` to locate the `.env` file relative to the script path:
```python
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)
```

## Risks / Trade-offs

- **[Risk]**: Shell configuration startup time.
  - **Mitigation**: Launching a login shell adds minimal overhead (<50ms) which is negligible for a persistent MCP server process.
- **[Risk]**: Shell environment variables not loaded if shell is not a login shell.
  - **Mitigation**: Specify the `-l` (login) flag explicitly in `args` to guarantee shell profile initialization.
