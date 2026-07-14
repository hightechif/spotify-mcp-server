import os
import functools
from typing import Optional, Callable, Any
from mcp.server.fastmcp import FastMCP
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables relative to script directory
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize FastMCP Server
mcp = FastMCP("spotify")

def get_spotify_client(access_token: Optional[str] = None) -> spotipy.Spotify:
    """Helper to initialize the Spotify Web API client."""
    if access_token:
        # Use dynamic OAuth token provided by the client (Phase 5)
        return spotipy.Spotify(auth=access_token)
    
    # Fallback to local OAuth flow or system credentials (Phase 1-4)
    client_id = os.getenv("SPOTIPY_CLIENT_ID") or os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET") or os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI") or os.getenv("SPOTIFY_REDIRECT_URI") or "http://127.0.0.1:8888/callback"
    
    if not client_id or not client_secret:
        raise ValueError("Missing SPOTIPY_CLIENT_ID or SPOTIPY_CLIENT_SECRET in environment variables.")

    scope = (
        "user-modify-playback-state "
        "user-read-playback-state "
        "user-read-currently-playing"
    )
    
    # Headless-safe auth manager
    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        open_browser=False
    )
    
    # Use refresh token from env if present to bypass interactive browser prompt
    refresh_token = os.getenv("SPOTIPY_REFRESH_TOKEN") or os.getenv("SPOTIFY_REFRESH_TOKEN")
    if refresh_token:
        try:
            token_info = auth_manager.refresh_access_token(refresh_token)
            return spotipy.Spotify(auth=token_info["access_token"])
        except Exception:
            pass # Fallback to standard flow if refresh fails
            
    return spotipy.Spotify(auth_manager=auth_manager)

def mcp_tool_guard(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to catch exceptions and return them in a standard dict format."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> dict:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return {"error": str(e)}
    return wrapper

def execute_playback_command(
    sp: spotipy.Spotify, 
    command_fn: Callable[..., Any], 
    *args: Any, 
    **kwargs: Any
) -> Any:
    """Executes a playback command, automatically transferring to an available device if needed."""
    try:
        return command_fn(*args, **kwargs)
    except Exception as err:
        if "NO_ACTIVE_DEVICE" in str(err) or "No active device" in str(err):
            devices = sp.devices().get("devices", [])
            if not devices:
                raise ValueError("No active or available Spotify devices found. Please open Spotify on a device.") from err
            
            device_id = devices[0].get("id")
            # Transfer playback to the first available device
            sp.transfer_playback(device_id=device_id, force_play=True)
            
            # Retry the command on the new active device
            kwargs["device_id"] = device_id
            return command_fn(*args, **kwargs)
        raise err

@mcp.tool()
@mcp_tool_guard
def get_current_playback(access_token: Optional[str] = None) -> dict:
    """Get information about the user's current Spotify playback state."""
    sp = get_spotify_client(access_token)
    playback = sp.current_playback()
    if not playback:
        return {"status": "No active playback device found."}
    return {
        "is_playing": playback.get("is_playing"),
        "track_name": playback.get("item", {}).get("name"),
        "artist_name": playback.get("item", {}).get("artists", [{}])[0].get("name"),
        "album_art": playback.get("item", {}).get("album", {}).get("images", [{}])[0].get("url"),
        "device_name": playback.get("device", {}).get("name"),
        "volume_percent": playback.get("device", {}).get("volume_percent"),
    }

@mcp.tool()
@mcp_tool_guard
def pause_playback(access_token: Optional[str] = None) -> dict:
    """Pause the current audio playback on Spotify."""
    sp = get_spotify_client(access_token)
    execute_playback_command(sp, sp.pause_playback)
    return {"status": "Playback paused successfully."}

@mcp.tool()
@mcp_tool_guard
def resume_playback(access_token: Optional[str] = None) -> dict:
    """Resume the current audio playback on Spotify."""
    sp = get_spotify_client(access_token)
    execute_playback_command(sp, sp.start_playback)
    return {"status": "Playback resumed successfully."}

@mcp.tool()
@mcp_tool_guard
def skip_next(access_token: Optional[str] = None) -> dict:
    """Skip to the next track on Spotify."""
    sp = get_spotify_client(access_token)
    execute_playback_command(sp, sp.next_track)
    return {"status": "Skipped to next track."}

@mcp.tool()
@mcp_tool_guard
def skip_previous(access_token: Optional[str] = None) -> dict:
    """Skip to the previous track on Spotify."""
    sp = get_spotify_client(access_token)
    execute_playback_command(sp, sp.previous_track)
    return {"status": "Skipped to previous track."}

@mcp.tool()
@mcp_tool_guard
def set_volume(volume_percent: int, access_token: Optional[str] = None) -> dict:
    """Set the playback volume percentage on Spotify."""
    sp = get_spotify_client(access_token)
    execute_playback_command(sp, sp.volume, volume_percent)
    return {"status": f"Volume set to {volume_percent}%."}

@mcp.tool()
@mcp_tool_guard
def search_spotify(query: str, type: str = "track", access_token: Optional[str] = None) -> dict:
    """Search Spotify's catalog for tracks or playlists."""
    sp = get_spotify_client(access_token)
    results = sp.search(q=query, limit=5, type=type)
    if not results:
        return {"results": []}
    if type == "track":
        items = results.get("tracks", {}).get("items", [])
        output = []
        for item in items:
            if not item:
                continue
            output.append({
                "name": item.get("name"),
                "artist": item.get("artists", [{}])[0].get("name"),
                "uri": item.get("uri"),
            })
        return {"results": output}
    elif type == "playlist":
        items = results.get("playlists", {}).get("items", [])
        output = []
        for item in items:
            if not item:
                continue
            output.append({
                "name": item.get("name"),
                "owner": item.get("owner", {}).get("display_name"),
                "uri": item.get("uri"),
            })
        return {"results": output}
    return {"error": f"Unsupported search type: {type}"}

@mcp.tool()
@mcp_tool_guard
def play_by_search(query: str, type: str = "track", access_token: Optional[str] = None) -> dict:
    """Play a track or playlist by searching for it first."""
    sp = get_spotify_client(access_token)
    results = sp.search(q=query, limit=1, type=type)
    if not results:
        return {"error": f"No results found for query '{query}'"}
    target_uri = None
    item_name = ""

    if type == "track":
        items = results.get("tracks", {}).get("items", [])
        items = [item for item in items if item is not None]
        if not items:
            return {"error": f"No tracks found matching '{query}'"}
        target_uri = items[0].get("uri")
        item_name = f"'{items[0].get('name')}' by {items[0].get('artists', [{}])[0].get('name')}"
    elif type == "playlist":
        items = results.get("playlists", {}).get("items", [])
        items = [item for item in items if item is not None]
        if not items:
            return {"error": f"No playlists found matching '{query}'"}
        target_uri = items[0].get("uri")
        item_name = f"playlist '{items[0].get('name')}'"
    else:
        return {"error": f"Unsupported playback search type: {type}"}

    # Attempt to play URI
    if type == "track":
        execute_playback_command(sp, sp.start_playback, uris=[target_uri])
    else:
        execute_playback_command(sp, sp.start_playback, context_uri=target_uri)
    return {"status": f"Now playing {item_name}."}

if __name__ == "__main__":
    mcp.run()
