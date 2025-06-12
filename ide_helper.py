# IDE Helper Script
# This file helps IDEs understand the project structure
# Add this to your Python path in your IDE settings if needed

import sys
import os
from pathlib import Path

# Add the tsapi package to the Python path
project_root = Path(__file__).parent.parent
tsapi_path = project_root / "tsapi" / "src"
sys.path.insert(0, str(tsapi_path))

# Now you can import tsapi modules
try:
    import tsapi
    import tsapi.auth
    from tsapi.http.base import ApiError, AuthenticationError, NetworkError
    print("All imports successful!")
except ImportError as e:
    print(f"Import error: {e}")
