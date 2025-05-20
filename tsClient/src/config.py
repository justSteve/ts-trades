from typing import Dict
import json
import requests
# client_app/config.py
import os
from pathlib import Path


# Get the client app's root directory
APP_ROOT = Path(__file__).parent

# Create a config directory inside your client app
CONFIG_DIR = APP_ROOT / 'secret'
TOKEN_PATH = CONFIG_DIR / 'ts_state.json'

# Create config directory if it doesn't exist
CONFIG_DIR.mkdir(exist_ok=True)

SCOPE = "openid offline_access profile MarketData ReadAccount Trade Matrix OptionSpreads"



def get_creds() -> Dict[str, str]:
    """
    Reads credentials from JSON file and returns client configuration.
    
    Returns:
        Dict[str, str]: Dictionary containing client_key, client_secret, and call_back_domain
    """
    credentials_path = CONFIG_DIR / 'credentials.json'

    if not credentials_path.exists():
        raise FileNotFoundError(
            f"Credentials file not found at {credentials_path}. "
            "Please ensure credentials.json exists in the secret directory."
        )

    try:
        with open(credentials_path) as f:
            credentials = json.load(f)

        required_fields = ['client_key', 'client_secret', 'call_back_domain']
        missing_fields = [
            field for field in required_fields if field not in credentials]

        if missing_fields:
            raise KeyError(
                f"Missing required fields in credentials.json: {', '.join(missing_fields)}"
            )

        return credentials

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in credentials.json: {str(e)}")
