#!/usr/bin/env python3
"""
Run tests with SQLite to avoid PostgreSQL connection conflicts
"""
import os
import sys
import subprocess
from pathlib import Path

# Set environment for SQLite testing
os.environ.update({
    "DEBUG": "true",
    "ENVIRONMENT": "test",
    "DATABASE_URL": "sqlite:///./test_db.sqlite",
    "REDIS_URL": "redis://localhost:6379/1",  # Will use fake redis
    "SECRET_KEY": "test-secret-key-for-testing-only",
    "ENCRYPTION_KEY": "test-encryption-key-32-chars-long!",
    "ENCRYPTION_SALT": "test-salt-for-encryption-purposes",
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "30"
})

print("🔧 Environment configured for SQLite:")
print(f"  DATABASE_URL: {os.environ['DATABASE_URL']}")
print(f"  ENCRYPTION_KEY: {os.environ['ENCRYPTION_KEY'][:10]}...")

def main():
    """Run pytest with SQLite configuration"""
    # Stop the uvicorn server first
    print("🛑 Please stop your uvicorn server (Ctrl+C) to avoid database conflicts")
    print("⏳ Waiting 5 seconds...")
    import time
    time.sleep(5)
    
    print("🧪 Running tests with SQLite...")
    
    # Run tests
    cmd = [
        sys.executable, "-m", "pytest", 
        "app/tests/smoke/", 
        "-v", 
        "--tb=short",
        "-x"  # Stop on first failure
    ]
    
    result = subprocess.run(cmd)
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())