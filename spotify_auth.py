import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
import httpx
from dotenv import load_dotenv

# Load dotenv relative to the directory where this script is located
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)



class SpotifyAuthError(Exception):
    """Raised when authentication with Spotify fails."""
    pass


class SpotifyPlayerNotFoundError(Exception):
    """Raised when there is no active Spotify playback session/device."""
    pass


class SpotifyClientError(Exception):
    """Raised when an API request to Spotify fails."""
    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class SpotifyAuth:
    """Manages Spotify OAuth credentials and handles automatic access token refreshing."""
    
    def __init__(self) -> None:
        self.client_id: str = os.environ.get("SPOTIFY_CLIENT_ID", "")
        self.client_secret: str = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
        self.refresh_token: str = os.environ.get("SPOTIFY_REFRESH_TOKEN", "")
        
        if not self.client_id or not self.client_secret or not self.refresh_token:
            raise SpotifyAuthError(
                "Missing Spotify credentials in environment. "
                "Ensure SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, and SPOTIFY_REFRESH_TOKEN are set."
            )
            
        self._access_token: Optional[str] = None
        self._expires_at: float = 0.0

    async def get_access_token(self, client: httpx.AsyncClient) -> str:
        """Retrieves the cached access token or refreshes it if expired."""
        # Refresh if token doesn't exist or is expiring within 30 seconds
        if not self._access_token or time.time() > (self._expires_at - 30):
            await self._refresh_access_token(client)
            
        assert self._access_token is not None
        return self._access_token

    async def _refresh_access_token(self, client: httpx.AsyncClient) -> None:
        """Requests a new access token from Spotify using the refresh token."""
        token_url = "https://accounts.spotify.com/api/token"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        try:
            response = await client.post(token_url, data=payload, headers=headers, timeout=10.0)
            if response.status_code != 200:
                raise SpotifyAuthError(f"Spotify token refresh returned HTTP {response.status_code}: {response.text}")
                
            data = response.json()
            self._access_token = data["access_token"]
            # Default to 3600 seconds if not provided
            expires_in = float(data.get("expires_in", 3600))
            self._expires_at = time.time() + expires_in
        except httpx.HTTPError as e:
            raise SpotifyAuthError(f"HTTP request to refresh Spotify token failed: {e}")


class SpotifyClient:
    """Wrapper around httpx.AsyncClient to execute authenticated calls to Spotify API."""
    
    def __init__(self) -> None:
        self.auth = SpotifyAuth()
        self.base_url = "https://api.spotify.com/v1"

    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None, 
        json_data: Optional[Dict[str, Any]] = None,
        retry_on_401: bool = True
    ) -> Dict[str, Any]:
        """Executes a request, appending authentication and handling errors/retries."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async with httpx.AsyncClient() as client:
            token = await self.auth.get_access_token(client)
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            try:
                response = await client.request(
                    method, 
                    url, 
                    headers=headers, 
                    params=params, 
                    json=json_data, 
                    timeout=10.0
                )
                
                # Check for token expiration
                if response.status_code == 401 and retry_on_401:
                    # Force token refresh on next get_access_token call
                    self.auth._access_token = None
                    self.auth._expires_at = 0.0
                    return await self._request(method, endpoint, params, json_data, retry_on_401=False)
                    
                # Active session issues
                if response.status_code == 404:
                    response_json = {}
                    try:
                        response_json = response.json()
                    except ValueError:
                        pass
                    
                    error_details = response_json.get("error", {})
                    # If Spotify returns player not found error
                    if "PLAYER" in error_details.get("reason", "").upper() or "NO ACTIVE DEVICE" in error_details.get("message", "").upper():
                        raise SpotifyPlayerNotFoundError(
                            "No active Spotify device found. Please open Spotify in your browser (open.spotify.com) "
                            "or open your Spotify app, play any track to activate it, and try again."
                        )
                        
                # Handle other client/server errors
                if response.status_code >= 400:
                    try:
                        error_msg = response.json()["error"]["message"]
                    except (KeyError, ValueError):
                        error_msg = response.text
                    raise SpotifyClientError(f"Spotify API error: {error_msg}", status_code=response.status_code)
                
                # Success checks
                if response.status_code in (204, 202) or not response.content.strip():
                    return {}  # No content returned
                
                try:
                    return response.json()  # type: ignore[no-any-return]
                except ValueError:
                    return {}  # Return empty dict if response is not JSON

                
            except httpx.HTTPError as e:
                raise SpotifyClientError(f"HTTP communication with Spotify failed: {e}")

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self._request("GET", endpoint, params=params)

    async def post(self, endpoint: str, params: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self._request("POST", endpoint, params=params, json_data=json_data)

    async def put(self, endpoint: str, params: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self._request("PUT", endpoint, params=params, json_data=json_data)

    async def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self._request("DELETE", endpoint, params=params)
