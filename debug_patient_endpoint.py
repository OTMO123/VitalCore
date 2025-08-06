#!/usr/bin/env python3
"""
Debug script to identify the exact issue with patient endpoint
"""

import sys
import traceback

def test_imports():
    """Test all imports that might be causing issues"""
    print("🔍 Testing imports...")
    
    try:
        print("1. Testing healthcare service import...")
        from app.modules.healthcare_records.service import get_healthcare_service
        print("✅ healthcare service import successful")
        
        print("2. Testing database imports...")
        from app.core.database_unified import get_db, init_db
        print("✅ database imports successful")
        
        print("3. Testing security imports...")
        from app.core.security import EncryptionService
        print("✅ security imports successful")
        
        print("4. Testing schemas...")
        from app.modules.healthcare_records.schemas import PatientCreate, PatientResponse
        print("✅ schema imports successful")
        
        print("5. Testing router imports...")
        from app.modules.healthcare_records.router import router
        print("✅ router import successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_database_models():
    """Test database model imports"""
    print("\n🔍 Testing database models...")
    
    try:
        from app.core.database_unified import Patient
        print("✅ Patient model import successful")
        
        # Check if we can access Patient fields
        print(f"Patient model attributes: {dir(Patient)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database model test failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    print("🚀 Debug Patient Endpoint Issues")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("❌ Import tests failed")
        return 1
    
    # Test database models
    if not test_database_models():
        print("❌ Database model tests failed")
        return 1
    
    print("\n✅ All basic tests passed")
    print("The issue might be runtime-related (database connection, etc.)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())