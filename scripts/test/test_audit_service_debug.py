#!/usr/bin/env python3
"""
Test audit service initialization
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

async def test_audit_service():
    """Test if audit service is initialized."""
    
    try:
        from app.modules.audit_logger.service import get_audit_service, audit_service
        print(f"Global audit_service variable: {audit_service}")
        
        try:
            service = get_audit_service()
            print(f"get_audit_service() returned: {service}")
        except RuntimeError as e:
            print(f"get_audit_service() failed: {e}")
        
        # Try to initialize manually
        print("Trying to initialize audit service manually...")
        from app.modules.audit_logger.service import initialize_audit_service
        from app.core.database import get_session_factory
        
        session_factory = get_session_factory()
        print(f"Session factory: {session_factory}")
        
        audit_service_instance = await initialize_audit_service(session_factory)
        print(f"Initialized audit service: {audit_service_instance}")
        
        # Try get_audit_service again
        try:
            service = get_audit_service()
            print(f"get_audit_service() after manual init: {service}")
        except RuntimeError as e:
            print(f"get_audit_service() still fails: {e}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_audit_service())