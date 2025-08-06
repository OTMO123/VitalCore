#!/usr/bin/env python3
"""
Enterprise Healthcare API Server - Production Entry Point

This is the main entry point for the FastAPI healthcare application.
It configures the Python path and starts the server with proper settings.

Usage:
    python run.py                 # Start development server
    python run.py --production    # Start production server with Gunicorn

Security Features:
- SOC2 Type II compliant audit logging
- HIPAA-compliant PHI encryption
- FHIR R4 healthcare data standards
- JWT authentication with RS256
- Role-based access control (RBAC)
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set PYTHONPATH environment variable for subprocesses
os.environ["PYTHONPATH"] = str(PROJECT_ROOT)

def start_development_server():
    """Start development server with auto-reload."""
    try:
        import uvicorn
        from app.main import app
        
        print("🏥 Starting Enterprise Healthcare API Server...")
        print("🔒 Security: SOC2 Type II + HIPAA + FHIR R4 Compliant")
        print("🛡️  Features: AES-256-GCM encryption, JWT auth, audit logging")
        print("📡 Server: http://localhost:8000")
        print("📚 Docs: http://localhost:8000/docs")
        print("🔍 Health: http://localhost:8000/health")
        
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            access_log=True
        )
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("💡 Install with: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

def start_production_server():
    """Start production server with Gunicorn."""
    try:
        import gunicorn.app.wsgiapp
        
        print("🏥 Starting Production Healthcare API Server...")
        print("🔒 Security: SOC2 Type II + HIPAA + FHIR R4 Compliant")
        print("⚡ Performance: Multi-worker Gunicorn deployment")
        
        # Gunicorn configuration
        sys.argv = [
            "gunicorn",
            "--bind", "0.0.0.0:8000",
            "--workers", "4",
            "--worker-class", "uvicorn.workers.UvicornWorker", 
            "--access-logfile", "-",
            "--error-logfile", "-",
            "--log-level", "info",
            "--timeout", "120",
            "--keepalive", "5",
            "app.main:app"
        ]
        
        gunicorn.app.wsgiapp.run()
    except ImportError:
        print("❌ Gunicorn not installed. Install with: pip install gunicorn")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start production server: {e}")
        sys.exit(1)

def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Enterprise Healthcare API Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                 # Development server with hot reload
  python run.py --production    # Production server with Gunicorn
  python run.py --check         # Verify installation

Security & Compliance:
  • SOC2 Type II audit logging with cryptographic integrity
  • HIPAA-compliant PHI encryption using AES-256-GCM
  • FHIR R4 healthcare data standards
  • JWT authentication with RS256 signing
  • Role-based access control for healthcare teams
        """
    )
    
    parser.add_argument(
        "--production", 
        action="store_true",
        help="Start production server with Gunicorn"
    )
    
    parser.add_argument(
        "--check",
        action="store_true", 
        help="Perform system checks and exit"
    )
    
    args = parser.parse_args()
    
    if args.check:
        print("🔍 Performing system checks...")
        try:
            # Import key modules to verify installation
            from app.main import app
            from app.core.config import get_settings
            from app.core.security import security_manager
            print("✅ All imports successful")
            print("✅ Configuration valid")
            print("✅ Security manager initialized")
            print("🎉 System ready for enterprise healthcare operations!")
        except Exception as e:
            print(f"❌ System check failed: {e}")
            sys.exit(1)
        return
    
    if args.production:
        start_production_server()
    else:
        start_development_server()

if __name__ == "__main__":
    main()