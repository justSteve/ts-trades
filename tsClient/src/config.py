#!/usr/bin/env python3
"""
Configuration module for the TradeStation client application.

This module provides configuration classes and utilities for credential
management, token storage, and logging.
"""
from typing import Dict, Optional, Any
import json
import os
from pathlib import Path
import logging
from datetime import datetime
import logging
from datetime import datetime

# Get the client app's root directory
APP_ROOT = Path(__file__).parent

# Create config directories inside the client app
# Create config directories inside the client app
CONFIG_DIR = APP_ROOT / 'secret'
LOGS_DIR = APP_ROOT / '..' / 'logs'
LOGS_DIR = APP_ROOT / '..' / 'logs'
TOKEN_PATH = CONFIG_DIR / 'ts_state.json'

# Create directories if they don't exist
# Create directories if they don't exist
CONFIG_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# OAuth2 scopes needed for TradeStation API
# OAuth2 scopes needed for TradeStation API
SCOPE = "openid offline_access profile MarketData ReadAccount Trade Matrix OptionSpreads"


class ClientCredentials:
    """
    Class for managing client credentials for TradeStation API access.
    """

    def __init__(self, credentials_path: Optional[Path] = None):
        """
        Initialize with the path to the credentials file.
        
        Args:
            credentials_path: Optional path to credentials file.
                Defaults to CONFIG_DIR/credentials.json
        """
        if credentials_path is None:
            credentials_path = CONFIG_DIR / 'credentials.json'

        self.credentials_path = credentials_path
        self._credentials = None
        self._logger = logging.getLogger(__name__)

    def get_client_key(self) -> str:
        """Return the client key (client ID) for API authentication."""
        return self._get_credentials()['client_key']

    def get_client_secret(self) -> str:
        """Return the client secret for API authentication."""
        return self._get_credentials()['client_secret']

    def get_redirect_uri(self) -> str:
        """Return the redirect URI for OAuth flow."""
        return self._get_credentials()['call_back_domain']

    def _get_credentials(self) -> Dict[str, str]:
        """
        Read credentials from JSON file.
        
        Returns:
            Dict[str, str]: Dictionary with credentials
            
        Raises:
            FileNotFoundError: If credentials file doesn't exist
            ValueError: If credentials file is invalid or missing required fields
        """
        # Return cached credentials if available
        if self._credentials is not None:
            return self._credentials

        if not self.credentials_path.exists():
            raise FileNotFoundError(
                f"Credentials file not found at {self.credentials_path}. "
                "Please ensure credentials.json exists in the secret directory."
            )

        try:
            self._logger.info(
                f"caller: Loading credentials from {self.credentials_path}")
            with open(self.credentials_path) as f:
                credentials = json.load(f)

            required_fields = ['client_key',
                               'client_secret', 'call_back_domain']
            missing_fields = [
                field for field in required_fields if field not in credentials]

            if missing_fields:
                raise KeyError(
                    f"Missing required fields in credentials.json: {', '.join(missing_fields)}"
                )

            self._credentials = credentials
            self._logger.info("caller: Successfully loaded credentials")
            return credentials

        except json.JSONDecodeError as e:
            self._logger.error(
                f"caller: Invalid JSON format in credentials.json: {str(e)}")
            raise ValueError(
                f"Invalid JSON format in credentials.json: {str(e)}")


class TokenStorage:
    """
    Class for managing token storage for TradeStation API.
    """

    def __init__(self, token_path: Path = TOKEN_PATH):
        """
        Initialize with the path to the token file.
        
        Args:
            token_path: Path to token file. Defaults to CONFIG_DIR/ts_state.json
        """
        self.token_path = token_path
        self._logger = logging.getLogger(__name__)

    def save_token(self, token_data: Dict[str, Any]) -> bool:
        """
        Save token data to storage.
        
        Args:
            token_data: Dictionary containing token information
            
        Returns:
            bool: Success or failure
        """
        try:
            self._logger.info(f"caller: Saving token to {self.token_path}")
            with open(self.token_path, "w") as f:
                json.dump(token_data, f, indent=4)
            self._logger.info("caller: Token saved successfully")
            return True
        except Exception as e:
            self._logger.error(f"caller: Failed to save token: {str(e)}")
            return False

    def load_token(self) -> Optional[Dict[str, Any]]:
        """
        Load token data from storage.
        
        Returns:
            Optional[Dict[str, Any]]: Token data if available, None otherwise
        """
        try:
            if not self.token_path.exists():
                self._logger.warning(
                    f"caller: Token file not found: {self.token_path}")
                return None

            self._logger.info(f"caller: Loading token from {self.token_path}")
            with open(self.token_path, "r") as f:
                token_data = json.load(f)
                self._logger.info("caller: Token loaded successfully")
                return token_data
        except Exception as e:
            self._logger.error(f"caller: Failed to load token: {str(e)}")
            return None


def setup_logging(log_to_file: bool = True) -> None:
    """
    Set up logging for the client application.
    
    Args:
        log_to_file: Whether to log to file in addition to console
    """
    # Create logs directory if it doesn't exist
    LOGS_DIR.mkdir(exist_ok=True)

    today = datetime.now()
    log_filename = f"{today.month:02d}-{today.day:02d}.csv"
    log_file = LOGS_DIR / log_filename

    # Add header to new log file if it doesn't exist
    if log_to_file and (not log_file.exists() or log_file.stat().st_size == 0):
        with open(log_file, 'w') as f:
            f.write("timestamp,level,logger,message\n")

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d %(levelname)s %(name)s: caller: %(message)s',
        '%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Optional file handler
    if log_to_file:
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(
            '%(asctime)s,%(levelname)s,%(name)s,%(message)s')
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)


class TokenStorage:
    """
    Class for managing token storage for TradeStation API.
    """
    
    def __init__(self, token_path: Path = TOKEN_PATH):
        """
        Initialize with the path to the token file.
        
        Args:
            token_path: Path to token file. Defaults to CONFIG_DIR/ts_state.json
        """
        self.token_path = token_path
        
    def save_token(self, token_data: Dict[str, Any]) -> bool:
        """
        Save token data to storage.
        
        Args:
            token_data: Dictionary containing token information
            
        Returns:
            bool: Success or failure
        """
        try:
            with open(self.token_path, "w") as f:
                json.dump(token_data, f, indent=4)
            return True
        except Exception as e:
            logging.error(f"Failed to save token: {str(e)}")
            return False
    
    def load_token(self) -> Optional[Dict[str, Any]]:
        """
        Load token data from storage.
        
        Returns:
            Optional[Dict[str, Any]]: Token data if available, None otherwise
        """
        try:
            if not self.token_path.exists():
                return None
                
            with open(self.token_path, "rb") as f:
                token_data = f.read()
                return json.loads(token_data.decode())
        except Exception as e:
            logging.error(f"Failed to load token: {str(e)}")
            return None


def setup_logging(log_to_file: bool = True) -> None:
    """
    Set up logging for the client application.
    
    Args:
        log_to_file: Whether to log to file in addition to console
    """
    # Create logs directory if it doesn't exist
    today = datetime.now()
    log_filename = f"{today.month:02d}-{today.day:02d}.csv"
    log_file = LOGS_DIR / log_filename
    
    # Add header to new log file if it doesn't exist
    if log_to_file and (not log_file.exists() or log_file.stat().st_size == 0):
        with open(log_file, 'w') as f:
            f.write("timestamp,level,logger,message\n")
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d %(levelname)s %(name)s: caller: %(message)s',
        '%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Optional file handler
    if log_to_file:
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter('%(asctime)s,%(levelname)s,%(name)s,%(message)s')
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    
def get_creds() -> Dict[str, str]:
    """
    Reads credentials from JSON file and returns client configuration.
    
    Returns:
        Dict[str, str]: Dictionary containing client_key, client_secret, and call_back_domain
    """
    return ClientCredentials()._get_credentials()


def get_token_storage() -> TokenStorage:
    """
    Get a TokenStorage instance for TradeStation API.
    
    Returns:
        TokenStorage: Instance for managing token storage
    """
    return TokenStorage()