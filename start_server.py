#!/usr/bin/env python3
"""
Start the IRIS Healthcare API server with proper configuration
"""
import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

if __name__ == "__main__":
    from app.main import app
    import uvicorn
    
    print("Starting IRIS Healthcare API Server...")
    print("Server URL: http://localhost:8004")
    print("API Documentation: http://localhost:8004/docs")
    print("Health Check: http://localhost:8004/health")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8004,
        reload=False,
        log_level="info"
    )