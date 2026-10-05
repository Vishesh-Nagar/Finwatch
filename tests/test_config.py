import json
import base64
import pytest
from bot.config import Config

def test_get_allowed_user_ids():
    Config.ALLOWED_USER_IDS_RAW = "12345, 67890, invalid, 111"
    user_ids = Config.get_allowed_user_ids()
    assert user_ids == {12345, 67890, 111}

    Config.ALLOWED_USER_IDS_RAW = ""
    assert Config.get_allowed_user_ids() == set()

def test_get_google_credentials_raw_json():
    dummy = {"type": "service_account", "project_id": "test-finwatch"}
    Config.GOOGLE_SERVICE_ACCOUNT_JSON = json.dumps(dummy)
    creds = Config.get_google_credentials_dict()
    assert creds == dummy

def test_get_google_credentials_base64():
    dummy = {"type": "service_account", "project_id": "base64-finwatch"}
    encoded = base64.b64encode(json.dumps(dummy).encode("utf-8")).decode("utf-8")
    Config.GOOGLE_SERVICE_ACCOUNT_JSON = encoded
    creds = Config.get_google_credentials_dict()
    assert creds == dummy
