#!/usr/bin/env python3
import os
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Any, Optional
import httpx
from dotenv import load_dotenv

# Load existing environment variables
load_dotenv()

PORT = int(os.environ.get("SPOTIFY_REDIRECT_PORT", "8888"))
REDIRECT_URI = f"http://127.0.0.1:{PORT}/callback"

# Scopes needed for full playback control and search status
SCOPES = [
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-read-currently-playing"
]

auth_code: Optional[str] = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        global auth_code
        parsed_url = urllib.parse.urlparse(self.path)
        
        if parsed_url.path == "/callback":
            query = urllib.parse.parse_qs(parsed_url.query)
            if "code" in query:
                auth_code = query["code"][0]
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"<html><body><h1>Authentication Successful!</h1>"
                    b"<p>You can close this tab and return to the terminal.</p></body></html>"
                )
            elif "error" in query:
                error_msg = query["error"][0]
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(
                    f"<html><body><h1>Authentication Failed!</h1><p>Error: {error_msg}</p></body></html>".encode()
                )
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress logging for clean terminal output
        pass


def exchange_code_for_tokens(client_id: str, client_secret: str, code: str) -> Optional[Dict[str, Any]]:
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    try:
        response = httpx.post(token_url, data=payload, headers=headers, timeout=10.0)
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]
    except Exception as e:
        print(f"\nError exchanging code for tokens: {e}", file=sys.stderr)
        if "response" in locals():
            print(f"Response: {response.text}", file=sys.stderr)
        return None


def main() -> None:
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("Error: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in your environment or .env file.")
        print("Please copy .env.example to .env and fill in your developer credentials first.")
        sys.exit(1)

    # 1. Start the HTTP server to listen for the callback
    server = HTTPServer(("127.0.0.1", PORT), CallbackHandler)
    
    # 2. Build the authorization URL
    auth_params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "show_dialog": "true"
    }
    authorize_url = f"https://accounts.spotify.com/authorize?{urllib.parse.urlencode(auth_params)}"

    print(f"Starting authentication flow...")
    print(f"Opening browser to: {authorize_url}\n")
    
    # 3. Open browser and wait for auth code callback
    webbrowser.open(authorize_url)
    
    print("Waiting for Spotify authorization redirect...")
    try:
        while auth_code is None:
            server.handle_request()
    except KeyboardInterrupt:
        print("\nAuthentication flow cancelled.")
        sys.exit(1)
    finally:
        server.server_close()

    if not auth_code:
        print("Failed to acquire authorization code.", file=sys.stderr)
        sys.exit(1)

    # 4. Exchange code for access & refresh tokens
    print("Exchanging authorization code for tokens...")
    tokens = exchange_code_for_tokens(client_id, client_secret, auth_code)
    
    if tokens and "refresh_token" in tokens:
        refresh_token = tokens["refresh_token"]
        print("\n" + "=" * 50)
        print("SUCCESSFULLY RETRIEVED REFRESH TOKEN")
        print("=" * 50)
        print(f"SPOTIFY_REFRESH_TOKEN={refresh_token}")
        print("=" * 50)
        print("\nAction Required:")
        print("1. Add this SPOTIFY_REFRESH_TOKEN to your `.env` file.")
        print("2. Your MCP server will now be able to authenticate and refresh its sessions automatically!\n")
    else:
        print("\nFailed to retrieve refresh token.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
