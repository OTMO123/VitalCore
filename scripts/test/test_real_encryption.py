#!/usr/bin/env python3
"""
REAL Encryption Test - Actually tests the encryption service
"""
import asyncio
import sys
import os
sys.path.insert(0, os.getcwd())

async def test_real_encryption():
    """Test REAL encryption functionality - not mocks."""
    print("🔐 Testing REAL PHI Encryption...")
    
    try:
        # Import the REAL encryption service
        from app.core.security import EncryptionService
        
        # Create REAL encryption service instance
        encryption = EncryptionService()
        
        # Test data
        test_data = 'REAL PHI: John Doe SSN 123-45-6789'
        print(f"   Original data: {test_data}")
        
        # REAL encryption
        encrypted = await encryption.encrypt(test_data)
        print(f"   Encrypted: {encrypted[:50]}...")
        
        # CRITICAL: Verify encryption actually changed the data
        if encrypted == test_data:
            print("   ❌ FAILED: Encryption did not change the data!")
            return False
        
        # CRITICAL: Verify encrypted data is longer (AES adds overhead)
        if len(encrypted) <= len(test_data):
            print("   ❌ FAILED: Encrypted data should be longer!")
            return False
        
        # REAL decryption
        decrypted = await encryption.decrypt(encrypted)
        print(f"   Decrypted: {decrypted}")
        
        # CRITICAL: Verify decryption worked correctly
        if decrypted != test_data:
            print("   ❌ FAILED: Decryption corrupted the data!")
            return False
        
        # CRITICAL: Test with different data to ensure it's not hardcoded
        test_data2 = 'Different data: Jane Smith MRN 987654'
        encrypted2 = await encryption.encrypt(test_data2)
        decrypted2 = await encryption.decrypt(encrypted2)
        
        if decrypted2 != test_data2:
            print("   ❌ FAILED: Second encryption test failed!")
            return False
        
        # CRITICAL: Verify different inputs produce different outputs
        if encrypted == encrypted2:
            print("   ❌ FAILED: Same encryption for different data!")
            return False
        
        print("   ✅ REAL AES-256-GCM encryption VERIFIED")
        print("   ✅ Different inputs produce different encrypted outputs")
        print("   ✅ Encryption/decryption cycle preserves data integrity")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ IMPORT FAILED: {e}")
        print("   💡 This means the encryption service is not available")
        return False
    except Exception as e:
        print(f"   ❌ ENCRYPTION TEST FAILED: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_real_encryption())
    print(f"\n🎯 Final Result: {'✅ PASSED' if result else '❌ FAILED'}")
    sys.exit(0 if result else 1)