"""
YouTube Upload Agent Module
============================
Uses YouTube Data API v3 to upload videos with optimized metadata.
Handles OAuth2 authentication and resumable uploads.
"""

import os
import time
import json
from typing import Optional
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from config import Config

MAX_RETRIES = 10
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]


class YouTubeAgent:
    """Handles YouTube video uploads via the Data API v3."""

    def __init__(self):
        self.client_id = Config.YOUTUBE_CLIENT_ID
        self.client_secret = Config.YOUTUBE_CLIENT_SECRET
        self.scopes = Config.YOUTUBE_SCOPES
        self.category_id = Config.YOUTUBE_CATEGORY_ID
        self.default_privacy = Config.YOUTUBE_DEFAULT_PRIVACY
        self.credentials_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "youtube_credentials.json"
        )
        self.token_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "youtube_token.json"
        )
        self.youtube = None

    def authenticate(self) -> bool:
        """Authenticate with YouTube using OAuth2."""
        try:
            creds = None
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    from google.auth.transport.requests import Request
                    creds.refresh(Request())
                else:
                    self._create_client_secrets()
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.scopes
                    )
                    creds = flow.run_local_server(port=8080)
                with open(self.token_file, "w") as token:
                    token.write(creds.to_json())
            self.youtube = build("youtube", "v3", credentials=creds)
            print("[YouTube] Authentication successful!")
            return True
        except Exception as e:
            print(f"[YouTube] Authentication failed: {e}")
            return False

    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list,
        category_id: Optional[str] = None,
        privacy_status: Optional[str] = None,
    ) -> dict:
        """
        Upload a video to YouTube with metadata.

        Args:
            video_path: Local path to the video file
            title: Video title (max 100 chars)
            description: Video description (max 5000 chars)
            tags: List of video tags
            category_id: YouTube category ID
            privacy_status: 'private', 'unlisted', or 'public'

        Returns:
            Dictionary with upload result (video_id, url)
        """
        if not self.youtube:
            if not self.authenticate():
                return {"error": "Authentication failed"}

        if not os.path.exists(video_path):
            return {"error": f"Video file not found: {video_path}"}

        category_id = category_id or self.category_id
        privacy_status = privacy_status or self.default_privacy

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags,
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(
            video_path, mimetype="video/mp4",
            resumable=True, chunksize=1024 * 1024,
        )

        try:
            print(f"[YouTube] Starting upload: '{title}'")
            print(f"[YouTube] File: {video_path}")
            print(f"[YouTube] Privacy: {privacy_status}")

            request = self.youtube.videos().insert(
                part="snippet,status", body=body, media_body=media,
            )
            response = self._resumable_upload(request)

            if response:
                video_id = response.get("id")
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                print(f"[YouTube] Upload successful!")
                print(f"[YouTube] Video URL: {video_url}")
                return {
                    "video_id": video_id,
                    "url": video_url,
                    "title": title,
                    "privacy_status": privacy_status,
                    "status": "uploaded",
                }
            return {"error": "Upload returned no response"}
        except HttpError as e:
            print(f"[YouTube] HTTP Error: {e}")
            return {"error": str(e)}
        except Exception as e:
            print(f"[YouTube] Error: {e}")
            return {"error": str(e)}

    def _resumable_upload(self, request) -> Optional[dict]:
        """Execute a resumable upload with retry logic."""
        response = None
        error = None
        retry = 0
        while response is None:
            try:
                print(f"[YouTube] Uploading...")
                status, response = request.next_chunk()
                if status:
                    print(f"[YouTube] Progress: {int(status.progress() * 100)}%")
            except HttpError as e:
                if e.resp.status in RETRIABLE_STATUS_CODES:
                    error = f"HTTP {e.resp.status}"
                else:
                    raise
            except Exception as e:
                error = str(e)
            if error:
                retry += 1
                if retry > MAX_RETRIES:
                    print(f"[YouTube] Max retries exceeded.")
                    return None
                sleep_time = min(2**retry, 64)
                print(f"[YouTube] Retry {retry}/{MAX_RETRIES} in {sleep_time}s...")
                time.sleep(sleep_time)
                error = None
        return response

    def _create_client_secrets(self):
        """Create OAuth client secrets file from environment variables."""
        config = {
            "installed": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uris": ["http://localhost:8080"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }
        with open(self.credentials_file, "w") as f:
            json.dump(config, f)

    def get_channel_info(self) -> dict:
        """Get information about the authenticated channel."""
        if not self.youtube:
            if not self.authenticate():
                return {"error": "Authentication failed"}
        try:
            resp = self.youtube.channels().list(
                part="snippet,statistics", mine=True
            ).execute()
            if resp.get("items"):
                ch = resp["items"][0]
                return {
                    "channel_id": ch["id"],
                    "title": ch["snippet"]["title"],
                    "subscribers": ch["statistics"].get("subscriberCount", "0"),
                    "video_count": ch["statistics"].get("videoCount", "0"),
                }
            return {"error": "No channel found"}
        except Exception as e:
            return {"error": str(e)}
