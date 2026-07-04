import logging
from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP

from spotify_auth import (
    SpotifyClient,
    SpotifyPlayerNotFoundError,
    SpotifyClientError,
    SpotifyAuthError
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("spotify-mcp-server")

# Initialize FastMCP Server
mcp = FastMCP("spotify")

# Instantiate our Spotify client
spotify_client = SpotifyClient()


async def get_target_device_id() -> Optional[str]:
    """Retrieves the best target device ID (prioritizing Web Players / Computers)."""
    try:
        devices_data = await spotify_client.get("me/player/devices")
        devices = devices_data.get("devices", [])
        if not devices:
            return None
            
        # 1. Prioritize active web player or computer browser session
        for device in devices:
            name = device.get("name", "").lower()
            device_type = device.get("type", "").lower()
            if "web player" in name or device_type == "computer":
                return str(device.get("id"))
                
        # 2. Fallback to any currently active device
        for device in devices:
            if device.get("is_active"):
                return str(device.get("id"))
                
        # 3. Fallback to the first available device
        return str(devices[0].get("id"))
    except Exception as e:
        logger.warning(f"Error querying active devices: {e}")
        return None


@mcp.resource("spotify://status")
async def get_spotify_status() -> str:
    """Returns a description of the currently playing track and player state."""
    try:
        playback = await spotify_client.get("me/player")
        if not playback or not playback.get("item"):
            return "Spotify Status: Not playing or player is inactive."
            
        item = playback["item"]
        track_name = item.get("name", "Unknown Track")
        artists = ", ".join([artist.get("name", "Unknown Artist") for artist in item.get("artists", [])])
        album = item.get("album", {}).get("name", "Unknown Album")
        is_playing = playback.get("is_playing", False)
        state_str = "Playing" if is_playing else "Paused"
        
        # Calculate progress
        progress_ms = playback.get("progress_ms", 0)
        duration_ms = item.get("duration_ms", 0)
        progress_sec = progress_ms // 1000
        duration_sec = duration_ms // 1000
        
        progress_str = f"{progress_sec // 60}:{progress_sec % 60:02d}"
        duration_str = f"{duration_sec // 60}:{duration_sec % 60:02d}"
        
        return (
            f"Spotify Status: {state_str}\n"
            f"Track: {track_name}\n"
            f"Artist(s): {artists}\n"
            f"Album: {album}\n"
            f"Progress: {progress_str} / {duration_str}"
        )
    except SpotifyPlayerNotFoundError:
        return "Spotify Status: Inactive (No active playback sessions found)."
    except Exception as e:
        return f"Spotify Status: Error retrieving state: {e}"


@mcp.prompt("vibe_check")
def vibe_check_prompt() -> str:
    """Guides the user through setting up a coding session playlist based on mood/task."""
    return (
        "I am currently coding and want to set a musical vibe. Please ask me about:\n"
        "1. What type of task I am working on (e.g., intense debugging, creative layout design, writing docs).\n"
        "2. My current energy level or mood (e.g., focused, tired, energetic, chill).\n"
        "3. My preferred genres or styles (e.g., lofi, electronic, synthwave, classical, rock).\n\n"
        "Once I respond, analyze my input and use the `search_spotify` or `get_recommendations` tool "
        "to find a suitable track or playlist, then start playing it immediately using the `play_by_search` tool."
    )


@mcp.tool()
async def get_current_playback() -> str:
    """Retrieve detailed information about the user's active playback, including the current track, volume, and active device."""
    try:
        playback = await spotify_client.get("me/player")
        if not playback:
            return "No active playback session found. Please start Spotify on a device."
            
        device = playback.get("device", {})
        device_name = device.get("name", "Unknown Device")
        device_type = device.get("type", "Unknown Type")
        volume = device.get("volume_percent", 0)
        
        status_text = await get_spotify_status()
        return (
            f"--- Active Device Info ---\n"
            f"Device: {device_name} ({device_type})\n"
            f"Volume: {volume}%\n\n"
            f"{status_text}"
        )
    except SpotifyPlayerNotFoundError as e:
        return str(e)
    except SpotifyClientError as e:
        return f"Failed to get current playback details: {e}"


@mcp.tool()
async def pause_playback() -> str:
    """Pause the current music playback on the active Spotify device."""
    try:
        device_id = await get_target_device_id()
        params = {"device_id": device_id} if device_id else None
        await spotify_client.put("me/player/pause", params=params)
        return "Playback paused successfully."
    except SpotifyPlayerNotFoundError as e:
        return str(e)
    except SpotifyClientError as e:
        # If it is already paused, Spotify might return a 403. Check and report nicely.
        if e.status_code == 403:
            return "Playback is already paused."
        return f"Failed to pause playback: {e}"


@mcp.tool()
async def resume_playback() -> str:
    """Resume the music playback on the active Spotify device."""
    try:
        device_id = await get_target_device_id()
        params = {"device_id": device_id} if device_id else None
        await spotify_client.put("me/player/play", params=params)
        return "Playback resumed successfully."
    except SpotifyPlayerNotFoundError as e:
        return str(e)
    except SpotifyClientError as e:
        # Already playing
        if e.status_code == 403:
            return "Playback is already active/playing."
        return f"Failed to resume playback: {e}"


@mcp.tool()
async def skip_next() -> str:
    """Skip to the next track in the user's Spotify queue."""
    try:
        device_id = await get_target_device_id()
        params = {"device_id": device_id} if device_id else None
        await spotify_client.post("me/player/next", params=params)
        return "Skipped to the next track."
    except SpotifyPlayerNotFoundError as e:
        return str(e)
    except SpotifyClientError as e:
        return f"Failed to skip to next track: {e}"


@mcp.tool()
async def skip_previous() -> str:
    """Skip back to the previous track in the user's Spotify queue."""
    try:
        device_id = await get_target_device_id()
        params = {"device_id": device_id} if device_id else None
        await spotify_client.post("me/player/previous", params=params)
        return "Skipped back to the previous track."
    except SpotifyPlayerNotFoundError as e:
        return str(e)
    except SpotifyClientError as e:
        return f"Failed to skip to previous track: {e}"


@mcp.tool()
async def set_volume(volume_percent: int) -> str:
    """Set the playback volume level on the active Spotify device.
    
    Args:
        volume_percent: The volume percentage to set (integer between 0 and 100 inclusive).
    """
    if not (0 <= volume_percent <= 100):
        return "Error: Volume percentage must be an integer between 0 and 100."
        
    try:
        device_id = await get_target_device_id()
        params = {
            "volume_percent": volume_percent,
            "device_id": device_id
        } if device_id else {"volume_percent": volume_percent}
        
        await spotify_client.put("me/player/volume", params=params)
        return f"Volume set to {volume_percent}%."
    except SpotifyPlayerNotFoundError as e:
        return str(e)
    except SpotifyClientError as e:
        return f"Failed to set volume: {e}"


@mcp.tool()
async def add_to_queue(uri: str) -> str:
    """Add a specific song/track to the playback queue by its Spotify track URI.
    
    Args:
        uri: The Spotify track URI, e.g., 'spotify:track:4PTG3Z6ehGkBF3zI7Y8G2y'.
    """
    if not uri.startswith("spotify:track:"):
        return "Error: Invalid track URI format. Track URIs must start with 'spotify:track:'."
        
    try:
        device_id = await get_target_device_id()
        params = {
            "uri": uri,
            "device_id": device_id
        } if device_id else {"uri": uri}
        
        await spotify_client.post("me/player/queue", params=params)
        return f"Track successfully added to queue."
    except SpotifyPlayerNotFoundError as e:
        return str(e)
    except SpotifyClientError as e:
        return f"Failed to add track to queue: {e}"


@mcp.tool()
async def search_spotify(query: str, type: str = "track,playlist", limit: int = 5) -> str:
    """Search for tracks, albums, artists, or playlists on Spotify.
    
    Args:
        query: The search query terms (e.g. 'synthwave focus' or 'lofi').
        type: Comma-separated list of item types to search for. Allowed values: 'track', 'album', 'artist', 'playlist'. Default is 'track,playlist'.
        limit: The maximum number of results to return per type (between 1 and 20). Default is 5.
    """
    params = {
        "q": query,
        "type": type,
        "limit": min(max(limit, 1), 20)
    }
    
    try:
        search_res = await spotify_client.get("search", params=params)
        output: List[str] = [f"Search results for '{query}':"]
        
        # Parse tracks
        if "tracks" in search_res and search_res["tracks"]["items"]:
            output.append("\n=== Tracks ===")
            for idx, track in enumerate(search_res["tracks"]["items"][:limit], 1):
                track_name = track.get("name", "Unknown Track")
                artists = ", ".join([artist.get("name", "Unknown Artist") for artist in track.get("artists", [])])
                uri = track.get("uri", "")
                output.append(f"{idx}. {track_name} by {artists} (URI: {uri})")
                
        # Parse playlists
        if "playlists" in search_res and search_res["playlists"]["items"]:
            output.append("\n=== Playlists ===")
            for idx, playlist in enumerate(search_res["playlists"]["items"][:limit], 1):
                playlist_name = playlist.get("name", "Unknown Playlist")
                owner = playlist.get("owner", {}).get("display_name", "Unknown Owner")
                uri = playlist.get("uri", "")
                output.append(f"{idx}. {playlist_name} by {owner} (URI: {uri})")
                
        # Parse albums
        if "albums" in search_res and search_res["albums"]["items"]:
            output.append("\n=== Albums ===")
            for idx, album in enumerate(search_res["albums"]["items"][:limit], 1):
                album_name = album.get("name", "Unknown Album")
                artists = ", ".join([artist.get("name", "Unknown Artist") for artist in album.get("artists", [])])
                uri = album.get("uri", "")
                output.append(f"{idx}. {album_name} by {artists} (URI: {uri})")
                
        if len(output) == 1:
            return "No matching tracks, playlists, or albums found."
            
        return "\n".join(output)
    except SpotifyClientError as e:
        return f"Failed to perform search: {e}"


@mcp.tool()
async def play_by_search(query: str, type: str = "track") -> str:
    """Search for a track, playlist, or album and immediately start playing the top match on the active device.
    
    Args:
        query: The search query, e.g., 'chill lo-fi beats'.
        type: The type of item to play. Allowed values: 'track', 'playlist', 'album'. Default is 'track'.
    """
    if type not in ("track", "playlist", "album"):
        return "Error: Type must be one of 'track', 'playlist', or 'album'."
        
    try:
        # 1. Search for the top item
        search_res = await spotify_client.get(
            "search", 
            params={"q": query, "type": type, "limit": 1}
        )
        
        type_plural = f"{type}s"
        items = search_res.get(type_plural, {}).get("items", [])
        if not items:
            return f"No matching {type} found for query '{query}'."
            
        top_item = items[0]
        uri = top_item.get("uri", "")
        item_name = top_item.get("name", "Unknown Name")
        
        # 2. Get target device ID
        device_id = await get_target_device_id()
        params = {"device_id": device_id} if device_id else None
        
        # 3. Formulate play request body
        if type == "track":
            json_body = {"uris": [uri]}
        else:
            json_body = {"context_uri": uri}
            
        await spotify_client.put("me/player/play", params=params, json_data=json_body)
        
        # Retrieve extra artist details if available for tracks/albums
        artist_details = ""
        if "artists" in top_item:
            artists = ", ".join([artist.get("name", "Unknown Artist") for artist in top_item.get("artists", [])])
            artist_details = f" by {artists}"
            
        return f"Successfully playing {type} '{item_name}'{artist_details} (URI: {uri}) on target device."
        
    except SpotifyPlayerNotFoundError as e:
        return str(e)
    except SpotifyClientError as e:
        return f"Failed to play '{query}' via search: {e}"


@mcp.tool()
async def get_recommendations(genres: str, limit: int = 5) -> str:
    """Retrieve track recommendations based on a comma-separated list of seed genres.
    
    Args:
        genres: Comma-separated list of up to 5 seed genres (e.g. 'lofi,chill,ambient' or 'electronic,synthwave').
        limit: The number of recommended tracks to return (between 1 and 20). Default is 5.
    """
    # Quick parameter cleanup
    genre_list = [g.strip() for g in genres.split(",") if g.strip()]
    if not genre_list:
        return "Error: Please specify at least one valid genre seed."
    if len(genre_list) > 5:
        return "Error: Spotify supports a maximum of 5 seed genres."
        
    params = {
        "seed_genres": ",".join(genre_list),
        "limit": min(max(limit, 1), 20)
    }
    
    try:
        res = await spotify_client.get("recommendations", params=params)
        tracks = res.get("tracks", [])
        if not tracks:
            return f"No recommendations found for seed genres: {genres}."
            
        output = [f"Recommended tracks based on genres [{genres}]:"]
        for idx, track in enumerate(tracks, 1):
            track_name = track.get("name", "Unknown Track")
            artists = ", ".join([artist.get("name", "Unknown Artist") for artist in track.get("artists", [])])
            uri = track.get("uri", "")
            output.append(f"{idx}. {track_name} by {artists} (URI: {uri})")
            
        return "\n".join(output)
    except SpotifyClientError as e:
        # Check if user passed invalid genre seeds
        if e.status_code == 400:
            return (
                f"Failed to get recommendations: {e}. "
                "Note: Make sure your genres match Spotify's official available genre list."
            )
        return f"Failed to get recommendations: {e}"


if __name__ == "__main__":
    # Start the FastMCP server when script is executed directly
    mcp.run()
