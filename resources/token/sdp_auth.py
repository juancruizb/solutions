import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load credentials from .env file (kb/.env)
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

# Path to store token data locally
TOKEN_FILE = Path(__file__).resolve().parent / "token_store.json"

# Zoho OAuth endpoint (domain configurable via .env)
ZOHO_DOMAIN = os.getenv("SDP_ZOHO_DOMAIN", "zoho.com")
ZOHO_TOKEN_URL = f"https://accounts.{ZOHO_DOMAIN}/oauth/v2/token"


class SDPAuth:
    """
    Manages OAuth 2.0 authentication for ServiceDesk Plus Cloud.
    Tokens expire, so this class handles automatic refresh.
    """

    @staticmethod
    def save_tokens(token_data: dict):
        """Persist token data to a local JSON file."""
        with open(TOKEN_FILE, "w") as f:
            json.dump(token_data, f, indent=2)

    @staticmethod
    def load_tokens() -> dict:
        """Load stored token data from local JSON file."""
        if not TOKEN_FILE.exists():
            return {}
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)

    @staticmethod
    def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> dict:
        """
        Use the refresh_token to obtain a new access_token from Zoho OAuth.
        Returns the full token response dict.
        """
        payload = {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        }
        response = requests.post(ZOHO_TOKEN_URL, data=payload)
        response.raise_for_status()
        token_data = response.json()

        # Merge with existing stored data so refresh_token is preserved
        existing = SDPAuth.load_tokens()
        existing.update(token_data)
        SDPAuth.save_tokens(existing)

        return token_data

    @staticmethod
    def get_access_token(client_id: str, client_secret: str) -> str:
        """
        Returns a valid access_token.
        Refreshes only when the token is older than 50 minutes (tokens last 60 min).
        Avoids hitting Zoho rate limits from refreshing on every request.
        """
        import time
        tokens = SDPAuth.load_tokens()

        acquired_at = tokens.get("acquired_at", 0)
        expires_in  = int(tokens.get("expires_in", 3600))
        age = time.time() - acquired_at

        # Reuse cached token if still fresh (with 10-min safety margin)
        if tokens.get("access_token") and age < (expires_in - 600):
            return tokens["access_token"]

        # Token expired or missing — refresh
        refresh_token = tokens.get("refresh_token") or os.getenv("SDP_REFRESH_TOKEN")
        if not refresh_token:
            raise ValueError(
                "No refresh_token found. Set SDP_REFRESH_TOKEN env var or run the initial OAuth flow."
            )

        token_data = SDPAuth.refresh_access_token(client_id, client_secret, refresh_token)

        # Persist with timestamp so next call can reuse it
        stored = SDPAuth.load_tokens()
        stored.update(token_data)
        stored["acquired_at"] = time.time()
        SDPAuth.save_tokens(stored)

        return token_data["access_token"]
