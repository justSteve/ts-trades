#!/usr/bin/env python3
"""
Quick test to verify tsapi is available
"""
import sys
print("Python path:")
for path in sys.path:
    print(f"  {path}")

print("\nTrying to import tsapi...")
try:
    import tsapi
    print("✅ tsapi imported successfully!")
    print(f"tsapi location: {tsapi.__file__}")
    
    print("\nTrying to import tsapi.auth...")
    import tsapi.auth
    print("✅ tsapi.auth imported successfully!")
    
    print("\nTrying to import exceptions...")
    from tsapi import ApiError, AuthenticationError, NetworkError
    print("✅ All imports successful!")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("\nThis means tsapi is not installed in the current Python environment.")
    print("Solutions:")
    print("1. Use Poetry: poetry run python src/test_imports.py")
    print("2. Install tsapi: pip install -e ../tsapi")
    print("3. Configure VS Code to use Poetry's virtual environment")
