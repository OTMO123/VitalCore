#!/usr/bin/env python3
"""
Quick setup for IRIS Healthcare Platform testing
"""

import asyncio
import os
import sys
import subprocess

def main():
    print("🚀 IRIS Healthcare Platform - Quick Setup")
    print("=" * 50)
    
    # Set environment for testing
    os.environ["DATABASE_URL"] = "postgresql://postgres:password@localhost:5432/iris_db"
    os.environ["ENVIRONMENT"] = "development"
    os.environ["DEBUG"] = "true"
    
    # Start the FastAPI application in test mode
    print("📋 Starting application in test mode...")
    
    try:
        # Use uvicorn to start the app with simpler setup
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n👋 Application stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()