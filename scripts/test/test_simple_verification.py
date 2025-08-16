#!/usr/bin/env python3
"""
Simple verification to check if we can import and run basic tests
"""
import sys
import os
sys.path.insert(0, os.getcwd())

def test_imports():
    """Test if we can import the required modules."""
    print("🔍 Testing Module Imports...")
    
    try:
        # Test encryption service import
        from app.core.security import EncryptionService
        print("   ✅ EncryptionService imported successfully")
        
        # Test database imports
        from app.core.database_unified import get_session_factory
        print("   ✅ Database session factory imported successfully")
        
        # Test models import
        from app.core.database_unified import Patient
        print("   ✅ Patient model imported successfully")
        
        # Test audit service import
        from app.modules.audit_logger.service import SOC2AuditService
        print("   ✅ SOC2AuditService imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def test_basic_functionality():
    """Test very basic functionality without async."""
    print("\n🧪 Testing Basic Functionality...")
    
    try:
        # Test simple encryption service creation
        from app.core.security import EncryptionService
        encryption = EncryptionService()
        print(f"   ✅ EncryptionService created: {type(encryption)}")
        
        # Test if it has the expected methods
        if hasattr(encryption, 'encrypt'):
            print("   ✅ encrypt method exists")
        else:
            print("   ❌ encrypt method missing")
            return False
            
        if hasattr(encryption, 'decrypt'):
            print("   ✅ decrypt method exists")
        else:
            print("   ❌ decrypt method missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Basic functionality test failed: {e}")
        return False

def main():
    """Run all verification tests."""
    print("🏥 SIMPLE VERIFICATION TEST")
    print("=" * 40)
    
    import_test = test_imports()
    basic_test = test_basic_functionality()
    
    print("\n" + "=" * 40)
    print("📊 VERIFICATION SUMMARY:")
    print(f"   Imports: {'✅ PASSED' if import_test else '❌ FAILED'}")
    print(f"   Basic Tests: {'✅ PASSED' if basic_test else '❌ FAILED'}")
    
    if import_test and basic_test:
        print("\n🎉 All verifications passed!")
        print("✅ Ready to run real functionality tests")
        return True
    else:
        print("\n⚠️ Some verifications failed")
        print("❌ Need to fix issues before running real tests")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)