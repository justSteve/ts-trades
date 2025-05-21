"""
This module provides a set of utilities for handling authentication with the TradeStation API.

It includes both synchronous and asynchronous client creation functions and token management utilities.

Functions:
- easy_client(): Easy client initialization either from a token file or by manual flow.
- client_from_access_functions(): Initialize a client using access functions.
- client_from_manual_flow(): Initialize a client by manually completing the OAuth2 flow.
- client_from_token_file(): Initialize a client by reading in a token file.

Example:
```python
from auth import easy_client

client = easy_client("client_key", "client_secret", "http://localhost/callback")
"""

import json
import logging
import os
import secrets
from typing import Any, Callable, Dict, Optional, Union
from urllib.parse import parse_qs, urlparse

import httpx
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from httpx import AsyncClient, Client, Response
from pathlib import Path

from .client.asynchronous import AsyncClient
from .client.synchronous import Client
from .logger import get_logger, log_api_call

AUTH_ENDPOINT = "https://signin.tradestation.com/authorize"
# nosec - This isn't a hardcoded password
TOKEN_ENDPOINT = "https://signin.tradestation.com/oauth/token"
AUDIENCE_ENDPOINT = "https://api.tradestation.com"

PAPER_ENDPOINT = "https://api.tradestation.com/v2/paper"
LIVE_ENDPOINT = "https://api.tradestation.com/v2/live"


class AuthError(Exception):
    """Exception raised for authentication errors."""
    pass


class CredentialProvider(ABC):
    """Abstract base class for credential providers.
    
    This allows clients to implement their own credential storage and retrieval
    mechanisms without the library knowing about storage locations.
    """
    
    @abstractmethod
    def get_client_key(self) -> str:
        """Return the client key (client ID) for API authentication."""
        pass
    
    @abstractmethod
    def get_client_secret(self) -> str:
        """Return the client secret for API authentication."""
        pass
    
    @abstractmethod
    def get_redirect_uri(self) -> str:
        """Return the redirect URI for OAuth flow."""
        pass


class TokenStorage(ABC):
    """Abstract base class for token storage.
    
    This allows clients to implement their own token storage mechanisms.
    """
    
    @abstractmethod
    def save_token(self, token_data: Dict[str, Any]) -> bool:
        """Save token data to storage.
        
        Args:
            token_data: Dictionary containing token information
            
        Returns:
            bool: Success or failure
        """
        pass
    
    @abstractmethod
    def load_token(self) -> Optional[Dict[str, Any]]:
        """Load token data from storage.
        
        Returns:
            Optional[Dict[str, Any]]: Token data if available, None otherwise
        """
        pass


class FileTokenStorage(TokenStorage):
    """Implementation of TokenStorage that uses a file for storage."""
    
    def __init__(self, token_path: str):
        """Initialize with token file path.
        
        Args:
            token_path: Path to the token file
        """
        self.token_path = token_path
        self.logger = get_logger(__name__, caller=False)
    
    def save_token(self, token_data: Dict[str, Any]) -> bool:
        """Save token data to a file.
        
        Args:
            token_data: Dictionary containing token information
            
        Returns:
            bool: Success or failure
        """
        try:
            self.logger.info(f"callee: Saving token to file {self.token_path}")
            with open(self.token_path, "w") as f:
                json.dump(token_data, f, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"callee: Failed to save token: {str(e)}")
            return False
    
    def load_token(self) -> Optional[Dict[str, Any]]:
        """Load token data from a file.
        
        Returns:
            Optional[Dict[str, Any]]: Token data if available, None otherwise
        """
        try:
            if not os.path.exists(self.token_path):
                self.logger.warning(f"callee: Token file not found: {self.token_path}")
                return None
                
            self.logger.info(f"callee: Loading token from file {self.token_path}")
            with open(self.token_path, "rb") as f:
                token_data = f.read()
                return json.loads(token_data.decode())
        except Exception as e:
            self.logger.error(f"callee: Failed to load token: {str(e)}")
            return None


def get_default_token_path() -> str:
    """Get the default token file path."""
    # On Windows: %APPDATA%\ts_py\ts_state.json
    # On Linux/Mac: ~/.config/ts_py/ts_state.json
    config_dir = os.path.join(os.path.expanduser('~'), '.config', 'ts_py')
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, 'ts_state.json')


def easy_client(
    credential_provider: Optional[CredentialProvider] = None,
    client_key: Optional[str] = None,
    client_secret: Optional[str] = None,
    redirect_uri: Optional[str] = None,
    token_storage: Optional[TokenStorage] = None,
    token_path: Optional[str] = None,
    paper_trade: bool = True,
    asyncio: bool = False
) -> Union[AsyncClient, Client]:
    """
    Initialize and return a client object based on existing token or manual flow.
    
    This function accepts either a CredentialProvider or directly provided credentials.
    It also accepts either a TokenStorage or a token_path for default file storage.

    Args:
        credential_provider: Optional provider for client credentials
        client_key: Optional client key (ID) if not using credential_provider
        client_secret: Optional client secret if not using credential_provider
        redirect_uri: Optional redirect URI if not using credential_provider
        token_storage: Optional TokenStorage implementation
        token_path: Optional path to token file if not using token_storage
        paper_trade: Whether to use paper trading (default: True)
        asyncio: Whether to return an async client (default: False)
        
    Returns:
        Client or AsyncClient instance
        
    Raises:
        ValueError: If neither credential_provider nor direct credentials are provided
    """
    logger = get_logger(__name__, caller=True)
    
    # Get credentials
    if credential_provider:
        key = credential_provider.get_client_key()
        secret = credential_provider.get_client_secret()
        redirect = credential_provider.get_redirect_uri()
    elif client_key and client_secret and redirect_uri:
        key = client_key
        secret = client_secret
        redirect = redirect_uri
    else:
        raise ValueError("Must provide either credential_provider or all of client_key, client_secret, and redirect_uri")
    
    # Set up token storage
    if token_storage is None:
        token_path = token_path or get_default_token_path()
        token_storage = FileTokenStorage(token_path)
    
    # Load token and create client
    token_data = token_storage.load_token()
    
    if token_data:
        logger.info("caller: Creating client from saved token")
        return client_from_token_data(
            key, secret, token_data, token_storage.save_token,
            paper_trade=paper_trade, asyncio=asyncio
        )
    else:
        logger.warning("caller: No token found, initiating manual flow")
        return client_from_manual_flow(
            key, secret, redirect,
            token_update_func=token_storage.save_token,
            paper_trade=paper_trade, asyncio=asyncio
        )


def client_from_manual_flow(
    client_key: str, 
    client_secret: str, 
    redirect_uri: str, 
    token_update_func: Optional[Callable[[Dict[str, Any]], bool]] = None,
    paper_trade: bool = True, 
    asyncio: bool = False
) -> Union[AsyncClient, Client]:
    """
    Initialize and return a client object by manually completing the OAuth2 flow.

    Parameters:
    - client_key (str): The client key for authentication.
    - client_secret (str): The client secret for authentication.
    - redirect_uri (str): The redirect URI for OAuth.
    - token_update_func (Callable, optional): Function to update token storage
    - paper_trade (bool, optional): Flag to indicate if the client should operate in paper trade mode. Default is True.
    - asyncio (bool, optional): Flag to indicate if the client should be asynchronous. Default is False.

    Returns:
    - AsyncClient | Client: An instance of either the AsyncClient or Client class,
        initialized with the provided tokens and settings.

    Example Usage:
    ```
    client = client_from_manual_flow("client_key", "client_secret", "http://localhost:80/", paper_trade=True, asyncio=False)
    ```

    Notes:
    - Follow the printed instructions to visit the authorization URL and paste the full redirect URL.
    - The function will automatically request tokens and initialize the client.
    """
    logger = get_logger(__name__, caller=True)
    logger.info("caller: Initiating manual OAuth flow")
    
    # Build the Authorization URL
    params = {
        "response_type": "code",
        "client_id": client_key,
        "redirect_uri": redirect_uri,
        "audience": AUDIENCE_ENDPOINT,
        # Ideally, this should be dynamically generated for each request
        "state": secrets.token_hex(16),
        "scope": "openid MarketData profile ReadAccount Trade Matrix OptionSpreads email offline_access",
    }
    
    try:
        url = httpx.get(AUTH_ENDPOINT, params=params).url
        print(f"Please go to this URL to authorize the application: {url}")
    
        # Obtain Authorization Code from User
        auth_redirect = input("Please enter the full redirect URL you were returned to: ")
        parsed_url = urlparse(auth_redirect)
        query_params = parse_qs(parsed_url.query)
        
        if 'code' not in query_params:
            raise AuthError("No authorization code found in the redirect URL")
        
        authorization_code = query_params.get("code", [])[0].strip()
    
        # Request Tokens Using Authorization Code
        payload = {
            "grant_type": "authorization_code",
            "client_id": client_key,
            "client_secret": client_secret,
            "code": authorization_code,
            "redirect_uri": redirect_uri,
        }
        headers = {"content-type": "application/x-www-form-urlencoded"}
        
        log_api_call(
            logger=logger,
            method="POST",
            endpoint=TOKEN_ENDPOINT,
            data=payload,
            headers=headers
        )
        
        response: httpx.Response = httpx.post(
            TOKEN_ENDPOINT, data=payload, headers=headers)
    
        if response.status_code != 200:
            error_msg = f"Failed to authorize token. {response.status_code}"
            logger.error(f"caller: {error_msg}")
            raise AuthError(error_msg)
    
        token: Dict[str, Union[str, int]] = response.json()
        logger.info("caller: Successfully obtained authorization token")
    
        # Update Token State if function provided
        if token_update_func:
            token_update_func(token)
    
        # Initialize the Client
        client_object: type[AsyncClient] | type[Client] = AsyncClient if asyncio else Client
    
        return client_object(
            client_id=client_key,
            client_secret=client_secret,
            paper_trade=paper_trade,
            _access_token=str(token.get("access_token")),
            _refresh_token=str(token.get("refresh_token")),
            _access_token_expires_in=int(token.get("expires_in", 0)),
            _access_token_expires_at=int(token.get("expires_at", 0)),
            _token_update_func=token_update_func,
        )
    except Exception as e:
        logger.error(f"caller: Authentication error: {str(e)}")
        raise


def client_from_token_data(
    client_key: str,
    client_secret: str, 
    token_data: Dict[str, Any],
    token_update_func: Optional[Callable[[Dict[str, Any]], bool]] = None,
    paper_trade: bool = True, 
    asyncio: bool = False
) -> Union[AsyncClient, Client]:
    """
    Initialize and return a client object based on token data.

    Parameters:
    - client_key (str): The client ID for authentication.
    - client_secret (str): The client secret for authentication.
    - token_data (Dict[str, Any]): Dictionary containing token information
    - token_update_func (Callable, optional): Function to update token storage
    - paper_trade (bool, optional): Flag to indicate if the client should operate in paper trade mode. Default is True.
    - asyncio (bool, optional): Flag to indicate if the client should be asynchronous. Default is False.

    Returns:
    - AsyncClient | Client: An instance of either the AsyncClient or Client class,
        initialized with the provided tokens and settings.
    """
    logger = get_logger(__name__, caller=True)
    logger.info("caller: Creating client from token data")
    
    client_object: type[AsyncClient] | type[Client] = AsyncClient if asyncio else Client
    
    return client_object(
        client_id=client_key,
        client_secret=client_secret,
        paper_trade=paper_trade,
        _access_token=token_data.get("access_token"),
        _refresh_token=token_data.get("refresh_token", ""),
        _access_token_expires_in=token_data.get("expires_in", 0),
        _access_token_expires_at=token_data.get("expires_at", 0),
        _token_update_func=token_update_func,
    )


def client_from_token_file(
    client_key: str, 
    client_secret: str, 
    token_path: str,
    paper_trade: bool = True, 
    asyncio: bool = False
) -> Union[AsyncClient, Client]:
    """
    Initialize and return a client object based on a given token file.

    Parameters:
    - client_key (str): The client ID for authentication.
    - client_secret (str): The client secret for authentication.
    - token_path (str): The file location for the token data.
    - paper_trade (bool, optional): Flag to indicate if the client should operate in paper trade mode. Default is True.
    - asyncio (bool, optional): Flag to indicate if the client should be asynchronous. Default is False.

    Returns:
    - AsyncClient | Client: An instance of either the AsyncClient or Client class,
        initialized with the provided tokens and settings.
    """
    token_storage = FileTokenStorage(token_path)
    token_data = token_storage.load_token()
    
    if not token_data:
        raise ValueError(f"No valid token data found in file: {token_path}")
        
    return client_from_token_data(
        client_key,
        client_secret,
        token_data,
        token_storage.save_token,
        paper_trade,
        asyncio
    )