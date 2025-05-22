# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project merges two components:

1. **tsAPI (ts-py)**: A wrapper library for the TradeStation API (forked from https://github.com/pattertj/ts-api)
2. **tsClient**: A client application that uses tsAPI to interact with TradeStation's trading platform

Long-term goal: Transition from original design to adopt conventions from [schwab-py](https://github.com/alexgolec/schwab-py).

## Architecture

The project follows a library-client model:
- **tsAPI**: Handles authentication, API communication, and data models
- **tsClient**: Provides configuration, user-facing functionality, and business logic

Current development priorities:
1. Refactor authentication so client can provide credentials without library knowing storage location
2. Standardize logging and error handling between client and API
3. Implement login flow leading to account details retrieval

## Development Commands

### tsAPI (Python Library)
```
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
```
# Install dependencies
cd tsClient
poetry install

# Run client
poetry run python src/main.py
```

## Logging Standards

- Log to CSV format in 'logs' folder with month-day format filename
- Prefix log messages with 'caller:' or 'callee:'
- Messages should reflect error conditions detected
- Document both input and outputs of messages in logs

## Security Notes

- Credentials are stored in tsClient/src/secret/credentials.json
- Token state is stored in ts_state.json
- Both components use OAuth2 authentication flow with TradeStation API