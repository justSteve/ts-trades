from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Union

PAPER_ENDPOINT = "https://api.tradestation.com/v2/paper"
AUDIENCE_ENDPOINT = "https://api.tradestation.com/v2/live"

from httpx import AsyncClient, Client, Response


@dataclass
class BaseStreamClient(ABC):
    """
    TradeStation Streaming API Client Class.

    Implements OAuth Authorization Code Grant workflow, handles configuration,
    and state management, adds token for authenticated calls, and performs streaming
    requests to the TradeStation API.

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
        self._base_resource = PAPER_ENDPOINT if self.paper_trade else AUDIENCE_ENDPOINT

    @abstractmethod
    async def connect(self) -> None:
        """Connect to the streaming API."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the streaming API."""
        pass

    @abstractmethod
    async def subscribe(self, channels: list[str]) -> None:
        """Subscribe to streaming channels."""
        pass

    @abstractmethod
    async def unsubscribe(self, channels: list[str]) -> None:
        """Unsubscribe from streaming channels."""
        pass

    def __repr__(self) -> str:
        """Define the string representation of our TradeStation Class instance.

        Returns:
        ----
        (str): A string representation of the client.
        """
        return f"<TradeStation Streaming Client (logged_in={self._logged_in}, authorized={self._auth_state})>"

    def _api_endpoint(self, url: str) -> str:
        """Create an API URL.

        Overview:
        ----
        Convert relative endpoint (e.g., 'quotes') to full API endpoint.

        Arguments:
        ----
        url (str): The relative endpoint.

        Returns:
        ----
        (str): The full API endpoint.
        """
        return f"{self._base_resource}/{url}"
