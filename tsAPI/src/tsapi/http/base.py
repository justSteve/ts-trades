"""BaseClient class for the TradeStation API with improved logging and error handling."""
from ..logger import get_logger, log_api_call, log_authentication_step, log_error_with_context
import json
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Callable, Dict, Mapping, Optional, Union

from httpx import Client, Response

AUTH_ENDPOINT = "https://signin.tradestation.com/authorize"
# nosec - This isn't a hardcoded password.
TOKEN_ENDPOINT = "https://signin.tradestation.com/oauth/token"
AUDIENCE_ENDPOINT = "https://api.tradestation.com/v3"
PAPER_ENDPOINT = "https://sim-api.tradestation.com/v3"


class TradeStationError(Exception):
    """Base exception for TradeStation API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 response: Optional[Dict[str, Any]] = None):
        """Initialize with error details.
        
        Args:
            message: Error message
            status_code: Optional HTTP status code
            response: Optional API response data
        """
        self.status_code = status_code
        self.response = response
        super().__init__(message)
        
    def __str__(self) -> str:
        """Return a detailed error message."""
        base_message = super().__str__()
        if self.status_code:
            base_message += f" (Status: {self.status_code})"
        return base_message


class AuthenticationError(TradeStationError):
    """Exception raised for authentication and authorization errors."""
    pass


class ApiError(TradeStationError):
    """Exception raised for API-related errors."""
    pass


class RateLimitError(TradeStationError):
    """Exception raised when API rate limits are exceeded."""
    pass


class NetworkError(TradeStationError):
    """Exception raised for network connectivity issues."""
    pass


@dataclass
class BaseClient(ABC):
    """
    TradeStation API Client Class.

    Implements OAuth Authorization Code Grant workflow, handles configuration,
    and state management, adds token for authenticated calls, and performs requests
    to the TradeStation API.

    Attributes:
        client_id (str): The client ID for authentication.
        client_secret (str): The client secret for authentication.
        paper_trade (bool): Flag to determine if the instance is for paper trading. Default is True.
        _logged_in (bool): Internal flag to track login status. Automatically initialized to False.
        _auth_state (bool): Internal flag to track authentication state. Automatically initialized to False.
        _access_token (Optional[str]): The access token for authentication. Initialized to None.
        _refresh_token (Optional[str]): The refresh token for authentication. Initialized to None.
        _access_token_expires_in (int): Time in seconds until the access token expires. Initialized to 0.
        _access_token_expires_at (float): Timestamp when the access token will expire. Initialized to 0.0.
        _base_resource (str): The base API endpoint for requests.
    """

    client_id: str
    client_secret: str
    paper_trade: bool = field(default=True)
    _logged_in: bool = field(init=False, default=False)
    _auth_state: bool = field(init=False, default=False)
    _access_token: Optional[str] = field(default=None)
    _refresh_token: Optional[str] = field(default=None)
    _access_token_expires_in: int = field(default=0)
    _access_token_expires_at: float = field(default=0.0)
    _token_read_func: Optional[Callable] = field(default=None)
    _token_update_func: Optional[Callable] = field(default=None)

    def __post_init__(self) -> None:
        """Initialize the base resource field and logger."""
        self._logger = get_logger(__name__)
        log_authentication_step(self._logger, "client initialization", True, 
                               f"Paper trade: {self.paper_trade}")
        
        self._base_resource = PAPER_ENDPOINT if self.paper_trade else AUDIENCE_ENDPOINT
        self._token_read_func = self._token_read if self._token_read_func is None else self._token_read_func
        self._token_update_func = self._token_save if self._token_update_func is None else self._token_update_func

    @abstractmethod
    def _delete_request(
        self, url: str, params: Optional[dict] = None, headers: Optional[dict] = None
    ) -> Union[Response, Any]:
        """Submit a delete request to TradeStation."""
        pass

    @abstractmethod
    def _get_request(
        self, url: str, params: Optional[dict] = None, headers: Optional[dict] = None
    ) -> Union[Response, Any]:
        """Submit a get request to TradeStation."""
        pass

    @abstractmethod
    def _post_request(
        self,
        url: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> Union[Response, Any]:
        """Submit a post request to TradeStation."""
        pass

    @abstractmethod
    def _put_request(
        self,
        url: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> Union[Response, Any]:
        """Submit a put request to TradeStation."""
        pass

    def __repr__(self) -> str:
        """Define the string representation of our TradeStation Class instance.

        Returns:
        ----
        (str): A string representation of the client.
        """
        return f"<TradeStation Client (logged_in={self._logged_in}, authorized={self._auth_state})>"

    def _api_endpoint(self, url: str) -> str:
        """Create an API URL.

        Overview:
        ----
        Convert relative endpoint (e.g., 'quotes') to full API endpoint.

        Arguments:
        ----
        url (str): The URL that needs conversion to a full endpoint URL.

        Returns:
        ---
        (str): A full URL.
        """
        # paper trading uses a different base url compared to regular trading.
        return f"{self._base_resource}/{url}"

    def _handle_error_response(self, response: Response, method: str, url: str) -> None:
        """Handle error responses from the API.
        
        Args:
            response: The HTTP response object
            method: The HTTP method used (GET, POST, etc.)
            url: The URL that was requested
            
        Raises:
            AuthenticationError: For 401, 403 errors
            RateLimitError: For 429 errors
            ApiError: For other API errors
        """
        status_code = response.status_code
        error_data = None
        
        try:
            error_data = response.json()
        except:
            error_content = response.text
        
        # Log detailed error information
        error_msg = f"{method} {url} - Status: {status_code}"
        if error_data:
            error_msg += f" - Details: {error_data}"
        
        log_api_call(
            logger=self._logger,
            method=method,
            endpoint=url,
            response=response,
            error=Exception(error_msg)
        )
        
        # Handle different error types
        if status_code == 401 or status_code == 403:
            raise AuthenticationError(
                f"Authentication error for {method} {url}", 
                status_code=status_code, 
                response=error_data
            )
        elif status_code == 429:
            raise RateLimitError(
                f"Rate limit exceeded for {method} {url}", 
                status_code=status_code, 
                response=error_data
            )
        else:
            error_message = f"API error for {method} {url}"
            if error_data and 'message' in error_data:
                error_message = f"{error_message}: {error_data['message']}"
            
            raise ApiError(
                error_message, 
                status_code=status_code, 
                response=error_data
            )

    def _grab_refresh_token(self) -> bool:
        """Refresh the current access token if it's expired.

        Returns:
        ----
        (bool): `True` if grabbing the refresh token was successful. `False` otherwise.
        """
        log_authentication_step(self._logger, "token refresh", True, "Starting token refresh")
        
        # Build the parameters of our request.
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
        }

        try:
            # Make a post request to the token endpoint.
            with Client() as client:
                log_api_call(
                    logger=self._logger,
                    method="POST",
                    endpoint=TOKEN_ENDPOINT,
                    data=data
                )
                
                response: Response = client.post(
                    url=TOKEN_ENDPOINT,
                    data=data,
                )

            # Save the token if the response was okay.
            if response.status_code == 200:
                self._token_save(response=response.json())
                log_authentication_step(self._logger, "token refresh", True, "Token refreshed successfully")
                return True
            else:
                log_authentication_step(self._logger, "token refresh", False, 
                                      f"HTTP {response.status_code}")
                return False
        except Exception as e:
            log_error_with_context(self._logger, e, "token refresh")
            return False

    def _token_save(self, response: dict) -> bool:
        """Save an access token or refresh token.

        Overview:
        ----
        Parses an access token from the response of a POST request and saves it
        in the state dictionary for future use. Additionally, it will store the
        expiration time and the refresh token.

        Arguments:
        ----
        response (requests.Response): A response object recieved from the `token_refresh` or `_grab_access_token`
            methods.

        Returns:
        ----
        (bool): `True` if saving the token was successful. `False` otherwise.
        """
        if self._update_token_variables(response):
            filename = "ts_state.json"

            state = {
                "access_token": self._access_token,
                "refresh_token": self._refresh_token,
                "expires_in": self._access_token_expires_in,
                "expires_at": self._access_token_expires_at,
            }

            # This is now used only as a fallback if no token_update_func is provided
            with open(file=filename, mode="w+") as state_file:
                json.dump(obj=state, fp=state_file, indent=4)

            # If a custom token update function is provided, use it
            if callable(self._token_update_func):
                try:
                    result = self._token_update_func(state)
                    log_authentication_step(self._logger, "token save", result, 
                                          "Custom token update function")
                    return result
                except Exception as e:
                    log_error_with_context(self._logger, e, "custom token update function")
                    return False

            log_authentication_step(self._logger, "token save", True, f"Saved to {filename}")
            return True

        return False

    def _token_read(self) -> Optional[Dict[str, Any]]:
        """Read in a token from file.

        Returns:
            Optional[Dict[str, Any]]: Token data if available, None if not found or error
        """
        try:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            filename = "ts_state.json"
            file_path = os.path.join(dir_path, filename)
            
            if not os.path.exists(file_path):
                self._logger.warning(f"Token file not found: {file_path}")
                return None
                
            with open(file=file_path, mode="r") as state_file:
                state = json.load(fp=state_file)
                
            log_authentication_step(self._logger, "token read", True, f"Read from {file_path}")
            return state
            
        except Exception as e:
            log_error_with_context(self._logger, e, "token read")
            return None

    def _update_token_variables(self, response: dict) -> bool:
        """Update the local variable from a given token response.

        Args:
            response (dict): Token response message

        Returns:
            bool: Success / Failure
        """
        # Save the access token.
        if "access_token" in response:
            self._access_token = response["access_token"]
            log_authentication_step(self._logger, "access token update", True, "Token updated")
        else:
            log_authentication_step(self._logger, "access token update", False, 
                                  "No access token in response")
            return False

        # If there is a refresh token then grab it.
        if "refresh_token" in response:
            self._refresh_token = response["refresh_token"]

        # Set the login state.
        self._logged_in = True
        self._auth_state = True

        # Store token expiration time.
        if "expires_in" in response:
            self._access_token_expires_in = response["expires_in"]
            self._access_token_expires_at = time.time() + int(response["expires_in"])
        else:
            # No expiration time in response, set a default (1 hour)
            self._access_token_expires_in = 3600
            self._access_token_expires_at = time.time() + 3600
            self._logger.warning("No token expiration time in response, using default")

        return True

    def _token_seconds(self) -> int:
        """Calculate when the token will expire.

        Overview:
        ----
        Return the number of seconds until the current access token or refresh token
        will expire. The default value is access token because this is the most commonly used
        token during requests.

        Returns:
        ----
        (int): The number of seconds till expiration
        """
        # Calculate the token expire time.
        token_exp = self._access_token_expires_at - time.time()

        # if the time to expiration is less than or equal to 0, return 0.
        return max(0, int(token_exp)) if self._refresh_token else 0

    def _token_validation(self, nseconds: int = 5) -> bool:
        """Validate the Access Token.

        Overview:
        ----
        Verify the current access token is valid for at least N seconds, and
        if not then attempt to refresh it. Can be used to assure a valid token
        before making a call to the Tradestation API.

        Arguments:
        ----
        nseconds (int): The minimum number of seconds the token has to be valid for before
            attempting to get a refresh token.
            
        Returns:
            bool: True if token is valid, False otherwise
        """
        if not self._access_token:
            log_authentication_step(self._logger, "token validation", False, "No access token available")
            return False
            
        seconds_left = self._token_seconds()
        
        if seconds_left < nseconds:
            log_authentication_step(self._logger, "token validation", True, 
                                  f"Token expires in {seconds_left}s, refreshing")
            return self._grab_refresh_token()
        else:
            self._logger.debug(f"Token valid for {seconds_left} more seconds")
            return True

    #############
    # Brokerage #
    #############

    def get_accounts(self, user_id: str) -> Response:
        """Grabs all the accounts associated with the User.

        Arguments:
        ----
        user_id (str): The Username of the account holder.

        Returns:
        ----
        (Response): All the user accounts.
        
        Raises:
            AuthenticationError: If authentication fails
            ApiError: If API returns an error
            NetworkError: If connection issues occur
        """
        method = "GET"
        endpoint = f"users/{user_id}/accounts"
        
        # validate the token.
        if not self._token_validation():
            raise AuthenticationError("Failed to validate access token")

        # define the endpoint.
        url_endpoint = self._api_endpoint(url=endpoint)

        # define the arguments
        params = {"access_token": self._access_token}

        try:
            log_api_call(
                logger=self._logger,
                method=method,
                endpoint=endpoint,
                params={"access_token": "***"}
            )
            
            response = self._get_request(url=url_endpoint, params=params)
            
            # Check for errors
            if response.status_code >= 400:
                self._handle_error_response(response, method, endpoint)
                
            log_api_call(
                logger=self._logger,
                method=method,
                endpoint=endpoint,
                response=response
            )
            
            return response
            
        except (AuthenticationError, ApiError, RateLimitError) as e:
            # Let these pass through
            raise
        except Exception as e:
            log_error_with_context(self._logger, e, f"get_accounts for user {user_id}")
            raise NetworkError(f"Network error accessing {endpoint}: {str(e)}")

    def get_balances(self, account_keys: list[str | int]) -> Response:
        """Grabs all the balances for each account provided.

        Args:
        ----
        account_keys (List[str]): A list of account numbers. Can only be a max
            of 25 account numbers

        Raises:
        ----
        ValueError: If the list is more than 25 account numbers will raise an error.
        AuthenticationError: If authentication fails
        ApiError: If API returns an error
        NetworkError: If connection issues occur

        Returns:
        ----
        Response: A list of account balances for each of the accounts.
        """
        method = "GET"
        
        # argument validation.
        account_keys_str = ""
        if not account_keys or not isinstance(account_keys, list):
            raise ValueError(
                "You must pass a list with at least one account for account keys.")
        elif len(account_keys) > 0 and len(account_keys) <= 25:
            account_keys_str = ",".join(map(str, account_keys))
        elif len(account_keys) > 25:
            raise ValueError(
                "You cannot pass through more than 25 account keys.")
                
        endpoint = f"brokerage/accounts/{account_keys_str}/balances"

        # validate the token.
        if not self._token_validation():
            raise AuthenticationError("Failed to validate access token")

        # define the endpoint.
        url_endpoint = self._api_endpoint(endpoint)

        # define the arguments
        params = {"access_token": self._access_token}

        try:
            log_api_call(
                logger=self._logger,
                method=method,
                endpoint=endpoint,
                params={"access_token": "***"}
            )
            
            response = self._get_request(url=url_endpoint, params=params)
            
            # Check for errors
            if response.status_code >= 400:
                self._handle_error_response(response, method, endpoint)
                
            log_api_call(
                logger=self._logger,
                method=method,
                endpoint=endpoint,
                response=response
            )
            
            return response
            
        except (AuthenticationError, ApiError, RateLimitError) as e:
            # Let these pass through
            raise
        except Exception as e:
            log_error_with_context(self._logger, e, f"get_balances for accounts {account_keys_str}")
            raise NetworkError(f"Network error accessing {endpoint}: {str(e)}")

    def get_positions(
        self, account_keys: list[str | int], symbols: Optional[list[str]] = None
    ) -> Response:
        """Grabs all the account positions.

        Arguments:
        ----
        account_keys (List[str]): A list of account numbers..

        symbols (List[str]): A list of ticker symbols, you want to return.

        Raises:
        ----
        ValueError: If the list is more than 25 account numbers will raise an error.
        AuthenticationError: If authentication fails
        ApiError: If API returns an error
        NetworkError: If connection issues occur

        Returns:
        ----
        Response: A list of account positions for each of the accounts.
        """
        method = "GET"
        
        # validate the token.
        if not self._token_validation():
            raise AuthenticationError("Failed to validate access token")

        # argument validation, account keys.
        account_keys_str = ""
        if not account_keys or not isinstance(account_keys, list):
            raise ValueError(
                "You must pass a list with at least one account for account keys.")
        elif len(account_keys) > 0 and len(account_keys) <= 25:
            account_keys_str = ",".join(map(str, account_keys))
        elif len(account_keys) > 25:
            raise ValueError(
                "You cannot pass through more than 25 account keys.")

        # argument validation, symbols.
        if symbols is None:
            params = {"access_token": self._access_token}
        elif not symbols:
            raise ValueError(
                "You cannot pass through an empty symbols list for the filter.")
        else:
            symbols_formatted = [f"Symbol eq {symbol!r}" for symbol in symbols]
            symbols_str = "or ".join(symbols_formatted)
            params = {"access_token": self._access_token,
                      "$filter": symbols_str}

        endpoint = f"brokerage/accounts/{account_keys_str}/positions"
            
        # define the endpoint.
        url_endpoint = self._api_endpoint(endpoint)

        try:
            log_api_call(
                logger=self._logger,
                method=method,
                endpoint=endpoint,
                params={k: "***" if k == "access_token" else v for k, v in params.items()}
            )
            
            response = self._get_request(url=url_endpoint, params=params)
            
            # Check for errors
            if response.status_code >= 400:
                self._handle_error_response(response, method, endpoint)
                
            log_api_call(
                logger=self._logger,
                method=method,
                endpoint=endpoint,
                response=response
            )
            
            return response
            
        except (AuthenticationError, ApiError, RateLimitError) as e:
            # Let these pass through
            raise
        except Exception as e:
            symbol_info = f" for symbols {symbols}" if symbols else ""
            log_error_with_context(self._logger, e, f"get_positions for accounts {account_keys_str}{symbol_info}")
            raise NetworkError(f"Network error accessing {endpoint}: {str(e)}")