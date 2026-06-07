"""
HeyGen Agent Module
====================
Uses HeyGen API to generate AI avatar videos from scripts.
Supports avatar selection, voice configuration, and video rendering.
"""

import requests
import time
import os
from typing import Optional
from config import Config


class HeyGenAgent:
    """Handles HeyGen AI video generation from scripts."""

    def __init__(self):
        self.api_key = Config.HEYGEN_API_KEY
        self.base_url = Config.HEYGEN_BASE_URL
        self.avatar_id = Config.HEYGEN_AVATAR_ID
        self.voice_id = Config.HEYGEN_VOICE_ID
        self.headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

    def list_avatars(self) -> list:
        """List available avatars from HeyGen."""
        try:
            response = requests.get(
                f"{self.base_url}/v2/avatars",
                headers=self.headers, timeout=30,
            )
            response.raise_for_status()
            return response.json().get("data", {}).get("avatars", [])
        except requests.exceptions.RequestException as e:
            print(f"[HeyGen] Error listing avatars: {e}")
            return []

    def list_voices(self) -> list:
        """List available voices from HeyGen."""
        try:
            response = requests.get(
                f"{self.base_url}/v2/voices",
                headers=self.headers, timeout=30,
            )
            response.raise_for_status()
            return response.json().get("data", {}).get("voices", [])
        except requests.exceptions.RequestException as e:
            print(f"[HeyGen] Error listing voices: {e}")
            return []

    def create_video(
        self,
        script: str,
        title: str = "AI Generated Video",
        avatar_id: Optional[str] = None,
        voice_id: Optional[str] = None,
        background_color: str = "#f5f5f5",
        aspect_ratio: str = "16:9",
    ) -> dict:
        """
        Create a video using HeyGen AI Studio API.

        Args:
            script: The video script/narration text
            title: Video title for internal reference
            avatar_id: HeyGen avatar ID (uses default if None)
            voice_id: HeyGen voice ID (uses default if None)
            background_color: Background color hex code
            aspect_ratio: Video aspect ratio

        Returns:
            Dictionary with video_id and status
        """
        avatar_id = avatar_id or self.avatar_id
        voice_id = voice_id or self.voice_id

        payload = {
            "video_inputs": [{
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "normal",
                },
                "voice": {
                    "type": "text",
                    "input_text": script,
                    "voice_id": voice_id,
                    "speed": 1.0,
                },
                "background": {
                    "type": "color",
                    "value": background_color,
                },
            }],
            "dimension": self._get_dimensions(aspect_ratio),
            "aspect_ratio": None,
            "title": title,
        }

        try:
            print(f"[HeyGen] Initiating video creation: '{title}'")
            response = requests.post(
                f"{self.base_url}/v2/video/generate",
                headers=self.headers, json=payload, timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            video_id = data.get("data", {}).get("video_id")
            if video_id:
                print(f"[HeyGen] Video creation started. ID: {video_id}")
                return {"video_id": video_id, "status": "processing"}
            return {"error": "No video_id returned", "response": data}
        except requests.exceptions.RequestException as e:
            print(f"[HeyGen] Error creating video: {e}")
            return {"error": str(e)}

    def check_video_status(self, video_id: str) -> dict:
        """Check the rendering status of a video."""
        try:
            response = requests.get(
                f"{self.base_url}/v1/video_status.get",
                headers=self.headers,
                params={"video_id": video_id}, timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return {
                "video_id": video_id,
                "status": data.get("data", {}).get("status", "unknown"),
                "video_url": data.get("data", {}).get("video_url", ""),
                "duration": data.get("data", {}).get("duration", 0),
            }
        except requests.exceptions.RequestException as e:
            return {"video_id": video_id, "status": "error", "error": str(e)}

    def wait_for_video(self, video_id: str) -> dict:
        """Poll until video is completed or timeout is reached."""
        print(f"[HeyGen] Waiting for video {video_id} to render...")
        attempts = 0
        while attempts < Config.MAX_POLL_ATTEMPTS:
            status_data = self.check_video_status(video_id)
            status = status_data.get("status", "")
            if status == "completed":
                print(f"[HeyGen] Video completed!")
                return status_data
            elif status in ("failed", "error"):
                print(f"[HeyGen] Video generation failed: {status_data}")
                return status_data
            attempts += 1
            print(f"[HeyGen] Status: {status} | Elapsed: {attempts * Config.POLL_INTERVAL}s")
            time.sleep(Config.POLL_INTERVAL)
        return {"video_id": video_id, "status": "timeout"}

    def download_video(self, video_url: str, output_path: Optional[str] = None) -> str:
        """Download the rendered video to local storage."""
        if not output_path:
            os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
            output_path = os.path.join(Config.OUTPUT_DIR, f"video_{int(time.time())}.mp4")
        try:
            print(f"[HeyGen] Downloading video to {output_path}...")
            response = requests.get(video_url, stream=True, timeout=300)
            response.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            size_mb = os.path.getsize(output_path) / 1024 / 1024
            print(f"[HeyGen] Download complete. Size: {size_mb:.2f} MB")
            return output_path
        except requests.exceptions.RequestException as e:
            print(f"[HeyGen] Error downloading video: {e}")
            return ""

    def _get_dimensions(self, aspect_ratio: str) -> dict:
        """Convert aspect ratio to pixel dimensions."""
        dims = {
            "16:9": {"width": 1920, "height": 1080},
            "9:16": {"width": 1080, "height": 1920},
            "1:1": {"width": 1080, "height": 1080},
        }
        return dims.get(aspect_ratio, {"width": 1920, "height": 1080})
