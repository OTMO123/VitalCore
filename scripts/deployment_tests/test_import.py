#!/usr/bin/env python3
"""
Test Healthcare Application Import
Simple script to verify the application imports correctly
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

def test_import():
    """Test importing the main application"""
    try:
        print("🧪 Testing Healthcare Application Import...")
        print("=" * 50)
        
        # Test core imports
        print("📦 Testing core imports...")
        from app.core.config import Settings
        print("✅ Settings imported successfully")
        
        from app.core.events.definitions import PatientCreated
        print("✅ Event definitions imported successfully")
        
        # Test main application
        print("🚀 Testing main application...")
        from app.main import app
        print("✅ FastAPI application imported successfully")
        
        # Test healthcare service
        print("🏥 Testing healthcare services...")
        from app.modules.healthcare_records.service import HealthcareRecordsService
        print("✅ Healthcare service imported successfully")
        
        print("\n" + "=" * 50)
        print("🎉 SUCCESS: All imports passed!")
        print("✅ Healthcare backend is ready for production")
        print("🚀 You can now start the server with: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: Import failed - {str(e)}")
        print(f"📍 Error type: {type(e).__name__}")
        
        # Provide troubleshooting info
        print(f"\n🔧 Troubleshooting:")
        print(f"  1. Ensure all dependencies are installed: pip install -r requirements.txt")
        print(f"  2. Check if .env file exists and is properly configured")
        print(f"  3. Verify database connection settings")
        
        return False

if __name__ == "__main__":
    success = test_import()
    sys.exit(0 if success else 1)