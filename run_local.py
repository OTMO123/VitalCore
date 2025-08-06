#!/usr/bin/env python3
"""
Local development server runner
Bypasses Docker for quick testing
"""
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables for local development
os.environ.update({
    "DEBUG": "true",
    "ENVIRONMENT": "development",
    "DATABASE_URL": "sqlite:///./local_dev.sqlite",
    "REDIS_URL": "redis://localhost:6379/1",  # Will use fake redis if not available
    "SECRET_KEY": "local-development-secret-key-not-for-production",
    "ENCRYPTION_KEY": "local-dev-encryption-key-32-chars!!",
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
    "ALLOWED_ORIGINS": '["*"]'
})

def main():
    """Start the FastAPI development server"""
    try:
        import uvicorn
        print("🚀 Starting FastAPI development server...")
        print("📍 Server will be available at: http://localhost:8000")
        print("📚 API documentation at: http://localhost:8000/docs")
        print("🔧 Press Ctrl+C to stop")
        print("-" * 60)
        
        # Import app after setting environment
        from app.main import app
        
        # Run with uvicorn
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError:
        print("❌ uvicorn not found. Installing...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "uvicorn[standard]"])
        
        # Try again
        import uvicorn
        from app.main import app
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())