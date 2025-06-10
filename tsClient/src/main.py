#!/usr/bin/env python3
"""
TradeStation Client Application

This application demonstrates how to use the tsAPI library to
authenticate with the TradeStation API and retrieve account information.
"""
from config import ClientCredentials, TokenStorage, setup_logging
from typing import List, Dict, Any, Optional
import json
import logging
import sys
import os
from pathlib import Path

# CRITICAL: Add the project root to Python path BEFORE any other imports
# Calculate the project root directory (ts-trades)
current_file = Path(__file__).resolve()  # tsClient/src/main.py
src_dir = current_file.parent            # tsClient/src/
tsclient_dir = src_dir.parent           # tsClient/
project_root = tsclient_dir.parent      # ts-trades/

# Debug: Print the paths to help troubleshoot
print(f"Current file: {current_file}")
print(f"Project root: {project_root}")
print(f"Looking for tsAPI at: {project_root / 'tsAPI'}")

# Add project root to sys.path so we can import tsAPI
sys.path.insert(0, str(project_root))

# Verify tsAPI directory exists
tsapi_path = project_root / 'tsAPI'
if not tsapi_path.exists():
    print(f"ERROR: tsAPI directory not found at {tsapi_path}")
    print("Please check your directory structure.")
    sys.exit(1)

# NOW we can import the modules

# Import tsAPI modules
try:
    from tsAPI.src import auth
    print("Successfully imported tsAPI auth module")
except ImportError as e:
    print(f"Failed to import tsAPI auth module: {e}")
    print("Current sys.path:")
    for path in sys.path:
        print(f"  {path}")
    sys.exit(1)

# Import client configuration

# Set up logging
setup_logging()
logger = logging.getLogger("tsClient")


# Define our own exception classes since they're not in the current base.py
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


class AuthenticationError(TradeStationError):
    """Exception raised for authentication and authorization errors."""
    pass


class ApiError(TradeStationError):
    """Exception raised for API-related errors."""
    pass


class NetworkError(TradeStationError):
    """Exception raised for network connectivity issues."""
    pass


class TradeStationClient:
    """
    Main client application for interacting with TradeStation API.
    
    This class handles authentication and provides methods for
    common TradeStation API operations.
    """

    def __init__(self,
                 credentials: Optional[ClientCredentials] = None,
                 token_storage: Optional[TokenStorage] = None,
                 paper_trade: bool = False,
                 user_id: Optional[str] = None):
        """
        Initialize the TradeStation client.
        
        Args:
            credentials: Optional credentials provider
            token_storage: Optional token storage provider
            paper_trade: Whether to use paper trading (default: True)
            user_id: User ID for TradeStation account (if not provided, will use from credentials)
        """
        self.credentials = credentials or ClientCredentials()
        self.token_storage = token_storage or TokenStorage()
        self.paper_trade = paper_trade
        self.user_id = user_id or self.credentials.get_user_id()
        self.client = None

        logger.info("TradeStation client initialized")

    def login(self) -> bool:
        """
        Log in to TradeStation API.
        
        This method authenticates with the TradeStation API using the 
        OAuth2 flow and creates a client object for making API calls.
        
        Returns:
            bool: True if login was successful, False otherwise
        """
        try:
            logger.info("Logging in to TradeStation API")

            # Get credentials
            client_key = self.credentials.get_client_key()
            client_secret = self.credentials.get_client_secret()
            redirect_uri = self.credentials.get_redirect_uri()

            # Create a custom token path using our token storage
            token_file = self.token_storage.token_path

            # Create client using the auth module's easy_client function
            self.client = auth.easy_client(
                client_key=client_key,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                token_path=str(token_file),
                paper_trade=self.paper_trade,
                asyncio=False  # Use synchronous client for now
            )

            # Validate token - note: _token_validation in current base.py returns None, not bool
            if self.client and hasattr(self.client, '_token_validation'):
                self.client._token_validation()
                logger.info("Token validation completed")
            else:
                logger.warning(
                    "Client created but token validation method not available")

            logger.info("Successfully logged in to TradeStation API")
            return True

        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            # Print more details for debugging
            import traceback
            traceback.print_exc()
            return False

    def get_user_accounts(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all accounts for the specified user ID.
        
        Args:
            user_id: Optional user ID. If not provided, uses the one set in constructor.
        
        Returns:
            List of account information dictionaries
        
        Raises:
            ValueError: If no user ID is provided and none is set in constructor
            AuthenticationError: If not authenticated
            ApiError: If API returns an error
            NetworkError: If connection issues occur
        """
        if self.client is None:
            raise AuthenticationError("Not logged in. Call login() first.")

        # Use provided user_id or fall back to instance variable
        user_id = user_id or self.user_id

        if not user_id:
            raise ValueError(
                "No user ID provided. Set it in constructor or provide to this method.")

        try:
            logger.info(f"Retrieving accounts for user {user_id}")

            # Get accounts from API
            response = self.client.get_accounts(user_id)

            if hasattr(response, 'status_code') and response.status_code == 200:
                accounts = response.json()
                logger.info(f"Found {len(accounts)} accounts")
                return accounts
            else:
                status_code = getattr(response, 'status_code', 'unknown')
                logger.error(f"Failed to get accounts: HTTP {status_code}")
                raise ApiError(f"Failed to get accounts",
                               status_code=status_code)

        except (AuthenticationError, ApiError, NetworkError) as e:
            logger.error(f"Error getting accounts: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting accounts: {str(e)}")
            raise NetworkError(f"Network error accessing accounts: {str(e)}")

    def get_account_balances(self, account_keys: List[str]) -> Dict[str, Any]:
        """
        Get balances for the specified accounts.
        
        Args:
            account_keys: List of account numbers to get balances for
        
        Returns:
            Dictionary with balance information
        
        Raises:
            AuthenticationError: If not authenticated
            ApiError: If API returns an error
            NetworkError: If connection issues occur
        """
        if self.client is None:
            raise AuthenticationError("Not logged in. Call login() first.")

        try:
            logger.info(
                f"Retrieving balances for accounts: {', '.join(account_keys)}")

            # Get balances from API
            response = self.client.get_balances(account_keys)

            if hasattr(response, 'status_code') and response.status_code == 200:
                balances = response.json()
                logger.info(f"Successfully retrieved balances")
                return balances
            else:
                status_code = getattr(response, 'status_code', 'unknown')
                logger.error(f"Failed to get balances: HTTP {status_code}")
                raise ApiError(f"Failed to get balances",
                               status_code=status_code)

        except (AuthenticationError, ApiError, NetworkError) as e:
            logger.error(f"Error getting balances: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting balances: {str(e)}")
            raise NetworkError(f"Network error accessing balances: {str(e)}")

    def get_account_positions(self, account_keys: List[str], symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get positions for the specified accounts.
        
        Args:
            account_keys: List of account numbers to get positions for
            symbols: Optional list of symbols to filter positions
        
        Returns:
            Dictionary with position information
        
        Raises:
            AuthenticationError: If not authenticated
            ApiError: If API returns an error
            NetworkError: If connection issues occur
        """
        if self.client is None:
            raise AuthenticationError("Not logged in. Call login() first.")

        try:
            symbol_str = f" for symbols: {', '.join(symbols)}" if symbols else ""
            logger.info(
                f"Retrieving positions for accounts: {', '.join(account_keys)}{symbol_str}")

            # Get positions from API
            response = self.client.get_positions(account_keys, symbols)

            if hasattr(response, 'status_code') and response.status_code == 200:
                positions = response.json()
                logger.info(f"Successfully retrieved positions")
                return positions
            else:
                status_code = getattr(response, 'status_code', 'unknown')
                logger.error(f"Failed to get positions: HTTP {status_code}")
                raise ApiError(f"Failed to get positions",
                               status_code=status_code)

        except (AuthenticationError, ApiError, NetworkError) as e:
            logger.error(f"Error getting positions: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting positions: {str(e)}")
            raise NetworkError(f"Network error accessing positions: {str(e)}")


def main():
    """
    Main function to demonstrate the TradeStation client.
    """
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='TradeStation API Client')
    parser.add_argument('--user-id', type=str, help='TradeStation user ID')
    parser.add_argument('--live', action='store_true',
                        help='Use live trading instead of paper trading')
    args = parser.parse_args()

    # Create client instance
    client = TradeStationClient(
        paper_trade=not args.live,
        user_id=args.user_id
    )

    try:
        # Login
        if not client.login():
            logger.error("Login failed. Exiting.")
            return 1

        # Get user ID from credentials if not provided
        user_id = args.user_id
        if not user_id:
            user_id = client.credentials.get_user_id()
            logger.info(f"Using user ID from credentials: {user_id}")

        # Get accounts
        accounts = client.get_user_accounts(user_id)

        # Print account information
        print("\nAccounts:")
        print("=========")
        for account in accounts:
            print(
                f"Account: {account.get('Name')} ({account.get('AccountID')})")
            print(f"Type: {account.get('Type')}")
            print(f"Status: {account.get('Status')}")
            print()

        # Get balances for first account
        if accounts:
            account_keys = [accounts[0].get('AccountID')]

            # Get balances
            balances = client.get_account_balances(account_keys)

            # Print balance information
            print("\nBalances:")
            print("=========")
            for balance in balances.get('Balances', []):
                print(f"Account: {balance.get('AccountID')}")
                print(f"Cash: ${balance.get('CashBalance', 0):.2f}")
                print(f"Equity: ${balance.get('Equity', 0):.2f}")
                print(f"Margin: ${balance.get('MarginBalance', 0):.2f}")
                print()

            # Get positions
            positions = client.get_account_positions(account_keys)

            # Print position information
            print("\nPositions:")
            print("==========")
            position_list = positions.get('Positions', [])
            if position_list:
                for position in position_list:
                    print(f"Symbol: {position.get('Symbol')}")
                    print(f"Quantity: {position.get('Quantity')}")
                    print(
                        f"Average Price: ${position.get('AveragePrice', 0):.2f}")
                    print(
                        f"Market Value: ${position.get('MarketValue', 0):.2f}")
                    print()
            else:
                print("No positions found.")

        return 0

    except AuthenticationError as e:
        logger.error(f"Authentication error: {str(e)}")
        return 1
    except ApiError as e:
        logger.error(f"API error: {str(e)}")
        return 1
    except NetworkError as e:
        logger.error(f"Network error: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
