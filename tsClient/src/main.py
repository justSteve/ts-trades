#!/usr/bin/env python3
"""
TradeStation Client Application

This application demonstrates how to use the tsAPI library to
authenticate with the TradeStation API and retrieve account information.
"""
import logging
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import custom modules
import tsAPI.auth as auth
from tsAPI.client.base import ApiError, AuthenticationError, NetworkError

# Import client configuration
from config import ClientCredentials, TokenStorage, setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger("tsClient")


class TradeStationClient:
    """
    Main client application for interacting with TradeStation API.
    
    This class handles authentication and provides methods for
    common TradeStation API operations.
    """
    
    def __init__(self, 
                credentials: Optional[ClientCredentials] = None,
                token_storage: Optional[TokenStorage] = None,
                paper_trade: bool = True,
                user_id: Optional[str] = None):
        """
        Initialize the TradeStation client.
        
        Args:
            credentials: Optional credentials provider
            token_storage: Optional token storage provider
            paper_trade: Whether to use paper trading (default: True)
            user_id: User ID for TradeStation account
        """
        self.credentials = credentials or ClientCredentials()
        self.token_storage = token_storage or TokenStorage()
        self.paper_trade = paper_trade
        self.user_id = user_id
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
            
            # Create client using credentials provider and token storage
            self.client = auth.easy_client(
                credential_provider=self.credentials,
                token_storage=self.token_storage,
                paper_trade=self.paper_trade
            )
            
            # Validate token
            if not self.client._token_validation():
                logger.error("Token validation failed")
                return False
                
            logger.info("Successfully logged in to TradeStation API")
            return True
            
        except AuthenticationError as e:
            logger.error(f"Authentication error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during login: {str(e)}")
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
            raise ValueError("No user ID provided. Set it in constructor or provide to this method.")
        
        try:
            logger.info(f"Retrieving accounts for user {user_id}")
            
            # Get accounts from API
            response = self.client.get_accounts(user_id)
            
            if response.status_code == 200:
                accounts = response.json()
                logger.info(f"Found {len(accounts)} accounts")
                return accounts
            else:
                logger.error(f"Failed to get accounts: HTTP {response.status_code}")
                raise ApiError(f"Failed to get accounts", status_code=response.status_code)
                
        except (AuthenticationError, ApiError, NetworkError) as e:
            logger.error(f"Error getting accounts: {str(e)}")
            raise
    
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
            logger.info(f"Retrieving balances for accounts: {', '.join(account_keys)}")
            
            # Get balances from API
            response = self.client.get_balances(account_keys)
            
            if response.status_code == 200:
                balances = response.json()
                logger.info(f"Successfully retrieved balances")
                return balances
            else:
                logger.error(f"Failed to get balances: HTTP {response.status_code}")
                raise ApiError(f"Failed to get balances", status_code=response.status_code)
                
        except (AuthenticationError, ApiError, NetworkError) as e:
            logger.error(f"Error getting balances: {str(e)}")
            raise
    
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
            logger.info(f"Retrieving positions for accounts: {', '.join(account_keys)}{symbol_str}")
            
            # Get positions from API
            response = self.client.get_positions(account_keys, symbols)
            
            if response.status_code == 200:
                positions = response.json()
                logger.info(f"Successfully retrieved positions")
                return positions
            else:
                logger.error(f"Failed to get positions: HTTP {response.status_code}")
                raise ApiError(f"Failed to get positions", status_code=response.status_code)
                
        except (AuthenticationError, ApiError, NetworkError) as e:
            logger.error(f"Error getting positions: {str(e)}")
            raise


def main():
    """
    Main function to demonstrate the TradeStation client.
    """
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='TradeStation API Client')
    parser.add_argument('--user-id', type=str, help='TradeStation user ID')
    parser.add_argument('--live', action='store_true', help='Use live trading instead of paper trading')
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
        
        # Get user ID if not provided
        user_id = args.user_id
        if not user_id:
            # In a real application, you might prompt for the user ID
            # or retrieve it from a configuration file
            user_id = "3535293"  # Example user ID
            logger.info(f"Using default user ID: {user_id}")
        
        # Get accounts
        accounts = client.get_user_accounts(user_id)
        
        # Print account information
        print("\nAccounts:")
        print("=========")
        for account in accounts:
            print(f"Account: {account.get('Name')} ({account.get('AccountID')})")
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
            for position in positions.get('Positions', []):
                print(f"Symbol: {position.get('Symbol')}")
                print(f"Quantity: {position.get('Quantity')}")
                print(f"Average Price: ${position.get('AveragePrice', 0):.2f}")
                print(f"Market Value: ${position.get('MarketValue', 0):.2f}")
                print()
        
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