"""
Configuration loader for the AI Video Agent.
Loads environment variables and provides default settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration for all API integrations."""

    # VidIQ Settings
    VIDIQ_API_KEY = os.getenv("VIDIQ_API_KEY", "")
    VIDIQ_BASE_URL = "https://api.vidiq.com/v1"

    # HeyGen Settings
    HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY", "")
    HEYGEN_BASE_URL = "https://api.heygen.com"
    HEYGEN_AVATAR_ID = os.getenv("HEYGEN_AVATAR_ID", "default")
    HEYGEN_VOICE_ID = os.getenv("HEYGEN_VOICE_ID", "default")

    # YouTube Settings
    YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
    YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
    YOUTUBE_CATEGORY_ID = os.getenv("YOUTUBE_CATEGORY_ID", "22")
    YOUTUBE_DEFAULT_PRIVACY = os.getenv("YOUTUBE_DEFAULT_PRIVACY", "private")
    YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

    # OpenAI Settings (for script enhancement)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # Agent Settings
    OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
    POLL_INTERVAL = 10
    MAX_POLL_ATTEMPTS = 120

    @classmethod
    def validate(cls, require_youtube=True):
        """Validate that all required API keys are configured."""
        errors = []
        if not cls.VIDIQ_API_KEY:
            errors.append("VIDIQ_API_KEY is not set")
        if not cls.HEYGEN_API_KEY:
            errors.append("HEYGEN_API_KEY is not set")
        if require_youtube:
            if not cls.YOUTUBE_CLIENT_ID:
                errors.append("YOUTUBE_CLIENT_ID is not set")
            if not cls.YOUTUBE_CLIENT_SECRET:
                errors.append("YOUTUBE_CLIENT_SECRET is not set")
        if errors:
            raise EnvironmentError(
                "Missing required configuration:\n" + "\n".join(f"  - {e}" for e in errors)
            )
        return True
