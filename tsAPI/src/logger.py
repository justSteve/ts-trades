"""
Logger configuration for the TradeStation API client.

This module provides logging functionality that follows the project's
standardized logging format, including CSV logging with timestamps
and caller/callee prefixes.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, Dict, Any


class CSVFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records in CSV format.
    
    Format: timestamp,log_level,logger_name,message
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a CSV line."""
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return f"{timestamp},{record.levelname},{record.name},{record.getMessage()}"


def get_logger(name: Optional[str] = None, caller: bool = True, 
               log_to_file: bool = True) -> logging.Logger:
    """
    Get a logger instance configured with standard settings.

    Args:
        name: Optional name for the logger. Defaults to 'ts' if None.
        caller: Boolean flag indicating if this is a caller or callee
                for message prefix purposes. Default is True (caller).
        log_to_file: Boolean flag to enable/disable file logging.
                    Default is True.

    Returns:
        A configured logging.Logger instance
    """
    logger = logging.getLogger(name or 'ts')
    
    # Set the prefix based on caller/callee status
    prefix = "caller:" if caller else "callee:"
    
    # Only add handlers if none exist to prevent duplicate handlers
    if not logger.handlers:
        # Console handler with standard formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            fmt=f'%(asctime)s.%(msecs)03d %(levelname)s %(name)s: {prefix} %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler with CSV formatting if enabled
        if log_to_file:
            # Create logs directory if it doesn't exist
            log_dir = Path('logs')
            log_dir.mkdir(exist_ok=True)
            
            # Create log file with month-day format
            today = datetime.now()
            log_filename = f"{today.month:02d}-{today.day:02d}.csv"
            file_path = log_dir / log_filename
            
            # Add header to new file if it doesn't exist or is empty
            if not file_path.exists() or file_path.stat().st_size == 0:
                with open(file_path, 'w') as f:
                    f.write("timestamp,level,logger,message\n")
            
            # Configure file handler
            file_handler = logging.FileHandler(file_path)
            file_formatter = CSVFormatter()
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        # Set default level to INFO
        logger.setLevel(logging.INFO)

    return logger


def log_api_call(logger: logging.Logger, 
                method: str, 
                endpoint: str, 
                params: Optional[Dict[str, Any]] = None,
                headers: Optional[Dict[str, Any]] = None,
                data: Optional[Dict[str, Any]] = None,
                response: Optional[Any] = None,
                error: Optional[Exception] = None) -> None:
    """
    Log API call details including input and output.
    
    Args:
        logger: Logger instance to use
        method: HTTP method used (GET, POST, etc.)
        endpoint: API endpoint called
        params: Optional query parameters
        headers: Optional request headers
        data: Optional request data/payload
        response: Optional response object
        error: Optional exception if the call failed
    """
    # Log the input
    input_msg = f"{method} {endpoint}"
    if params:
        # Filter out sensitive information like access_token
        filtered_params = {k: v for k, v in params.items() if k.lower() != 'access_token'}
        input_msg += f", params: {filtered_params}"
    
    if data:
        # Filter out sensitive information
        filtered_data = {k: '***' if k.lower() in ['client_secret', 'password', 'token'] else v 
                        for k, v in data.items()}
        input_msg += f", data: {filtered_data}"
    
    logger.info(f"API Request: {input_msg}")
    
    # Log the output
    if error:
        logger.error(f"API Error: {method} {endpoint} - {str(error)}")
    elif response:
        # Log status code
        if hasattr(response, 'status_code'):
            status = getattr(response, 'status_code')
            logger.info(f"API Response: {method} {endpoint} - Status: {status}")