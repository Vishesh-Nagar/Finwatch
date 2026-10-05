import os
import json
import base64
from typing import Set, Optional, Dict, Any
from dotenv import load_dotenv

# Load local .env if present
load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    SPREADSHEET_ID: str = os.getenv("SPREADSHEET_ID", "").strip()
    SHEET_NAME: str = os.getenv("SHEET_NAME", "Transactions").strip()
    GOOGLE_SERVICE_ACCOUNT_FILE: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials.json").strip()
    GOOGLE_SERVICE_ACCOUNT_JSON: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    
    # Comma-separated list of Telegram user IDs
    ALLOWED_USER_IDS_RAW: str = os.getenv("ALLOWED_TELEGRAM_USER_IDS", "").strip()

    @classmethod
    def get_allowed_user_ids(cls) -> Set[int]:
        if not cls.ALLOWED_USER_IDS_RAW:
            return set()
        user_ids = set()
        for item in cls.ALLOWED_USER_IDS_RAW.split(","):
            item = item.strip()
            if item.isdigit():
                user_ids.add(int(item))
        return user_ids

    @classmethod
    def get_google_credentials_dict(cls) -> Optional[Dict[str, Any]]:
        """
        Loads Google Service Account credentials either from:
        1. GOOGLE_SERVICE_ACCOUNT_JSON env var (raw JSON or base64 encoded)
        2. GOOGLE_SERVICE_ACCOUNT_FILE path (local credentials.json)
        """
        if cls.GOOGLE_SERVICE_ACCOUNT_JSON:
            raw = cls.GOOGLE_SERVICE_ACCOUNT_JSON.strip()
            # Try raw JSON first
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass
            # Try base64 decoded JSON
            try:
                decoded = base64.b64decode(raw).decode("utf-8")
                return json.loads(decoded)
            except Exception:
                pass

        if cls.GOOGLE_SERVICE_ACCOUNT_FILE and os.path.exists(cls.GOOGLE_SERVICE_ACCOUNT_FILE):
            with open(cls.GOOGLE_SERVICE_ACCOUNT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)

        return None

    @classmethod
    def validate(cls) -> Dict[str, bool]:
        """Returns readiness status for all external dependencies."""
        return {
            "telegram_token_present": bool(cls.TELEGRAM_BOT_TOKEN),
            "gemini_api_key_present": bool(cls.GEMINI_API_KEY),
            "spreadsheet_id_present": bool(cls.SPREADSHEET_ID),
            "google_credentials_present": cls.get_google_credentials_dict() is not None,
            "has_allowed_users": len(cls.get_allowed_user_ids()) > 0,
        }
