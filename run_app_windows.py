#!/usr/bin/env python3
"""
Windows-compatible FastAPI app runner
Runs the app without Unicode console issues.
"""
import os
import sys
import asyncio
import uvicorn

# Set environment to avoid Unicode issues
os.environ['PYTHONIOENCODING'] = 'utf-8'

if __name__ == "__main__":
    print("Starting FastAPI application...")
    print("Clinical Workflows module integrated!")
    print("Available endpoints:")
    print("  - http://localhost:8000/api/v1/clinical-workflows/health")
    print("  - http://localhost:8000/api/v1/clinical-workflows/")
    print("  - http://localhost:8000/docs (API documentation)")
    
    try:
        # Run the app directly
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=["app"],
            log_level="info"
        )
    except KeyboardInterrupt:
        print("Application stopped by user")
    except Exception as e:
        print(f"Error starting application: {e}")