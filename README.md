# TS-Trades: TradeStation API Client

This project provides a Python client for interacting with the TradeStation API. It consists of two main components:

1. **tsAPI** - A Python wrapper library for the TradeStation API
2. **tsClient** - A client application that uses tsAPI to interact with TradeStation

## Features

- OAuth2 authentication with TradeStation API
- Account information retrieval
- Balance and position tracking
- Paper trading support
- Standardized logging with CSV output
- Secure credential management
- Token state persistence

## Prerequisites

- Python 3.8 or higher
- TradeStation account with API access
- TradeStation API credentials (client key and secret)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/justSteve/ts-trades
   cd ts-trades
   ```

2. Install the tsAPI package:
   ```
   cd tsAPI
   poetry install
   ```

3. Install the tsClient package:
   ```
   cd ../tsClient
   poetry install
   ```

## Configuration

~~1. Create a credentials file at `tsClient/src/secret/credentials.json`:~~
1. Create a credentials file at `secret/credentials.json`:
   ```json
   {
       "client_key": "YOUR_CLIENT_KEY",
       "client_secret": "YOUR_CLIENT_SECRET",
       "call_back_domain": "http://localhost:3000"
   }
   ```

   Replace `YOUR_CLIENT_KEY` and `YOUR_CLIENT_SECRET` with your TradeStation API credentials.

## Usage

### Running the Client

From the tsClient directory:

```bash
poetry run python src/main.py
```

Command line options:
- `--user-id USER_ID`: Specify your TradeStation user ID
- `--live`: Use live trading instead of paper trading (default is paper trading)

### Example Usage in Code

```python
from tsClient.src.config import ClientCredentials, TokenStorage, setup_logging
from tsClient.src.main import TradeStationClient

# Set up logging
setup_logging()

# Create client instance
client = TradeStationClient(
    paper_trade=True,  # Use paper trading
    user_id="YOUR_USER_ID"  # Optional, can be provided later
)

# Login
if client.login():
    # Get accounts
    accounts = client.get_user_accounts("YOUR_USER_ID")
    
    # Get account balances
    if accounts:
        account_keys = [accounts[0].get('AccountID')]
        balances = client.get_account_balances(account_keys)
        
        # Get positions
        positions = client.get_account_positions(account_keys)
```

## Project Structure

```
ts-trades/
│── secret/
│       └── credentials.json  # API credentials
│
├── tsAPI/                   # TradeStation API wrapper
│   ├── src/
│   │   ├── auth.py          # Authentication utilities
│   │   ├── client/
│   │   │   ├── base.py      # Base client with error handling
│   │   │   ├── synchronous.py  # Synchronous client
│   │   │   ├── asynchronous.py # Async client
│   │   │   └── baseStream.py   # Streaming client base
│   │   └── logger.py        # Logging utilities
│   └── poetry.lock, pyproject.toml   # Package configuration
│
└── tsClient/                # Client application
    ├── src/
    │   ├── config.py        # Client configuration
    │   ├── main.py          # Main client application
    └── poetry.lock, pyproject.toml   # Package configuration
```

## Development

### tsAPI (Python Library)
```bash
# Install dependencies
cd tsAPI
poetry install

# Run tests
poetry run pytest

# Lint code
poetry run black .
poetry run isort .
poetry run mypy .
poetry run ruff .

# Build package
poetry build
```

### tsClient (Application)
```bash
# Install dependencies
cd tsClient
poetry install

# Run client
poetry run python src/main.py
```

## Logging

Logs are stored in CSV format in the 'logs' folder with month-day format filenames (e.g., 05-21.csv). 
Log messages are prefixed with 'caller:' or 'callee:' to indicate the source and reflect error conditions detected.
The logs document both inputs and outputs of API calls for better traceability.

## Security Notes

~~- Credentials are stored securely in tsClient/src/secret/credentials.json~~
- Credentials are stored securely in secret/credentials.json
- Token state is stored in secret/ts_state.json
- Both components use OAuth2 authentication flow with TradeStation API

## Current Development Focus

The current development priorities are:
1. Refactor authentication so client can provide credentials without library knowing storage location
2. Standardize logging and error handling between client and API
3. All logs should be stored in the logs folder of the project root with month-day format filenames (e.g., client-05-21.csv or api-05-21.csv)
4. Implement login flow leading to account details retrieval

## Long-term Goals

Transition from original design to adopt conventions from [schwab-py](https://github.com/alexgolec/schwab-py).
