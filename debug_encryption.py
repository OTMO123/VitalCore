#!/usr/bin/env python3
"""
Debug script to understand the encryption service behavior.
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.security import EncryptionService

async def main():
    encryption_service = EncryptionService()
    
    # Test basic encryption
    test_data = "test data"
    print(f"Original data: {test_data}")
    
    encrypted = await encryption_service.encrypt(test_data)
    print(f"Encrypted data: {encrypted}")
    print(f"Encrypted type: {type(encrypted)}")
    print(f"Encrypted length: {len(encrypted)}")
    
    # Check if it starts with Fernet format
    print(f"Starts with 'gAAAAA': {encrypted.startswith('gAAAAA')}")
    
    # Try to decrypt
    try:
        decrypted = await encryption_service.decrypt(encrypted)
        print(f"Decrypted data: {decrypted}")
        print(f"Decryption successful: {decrypted == test_data}")
    except Exception as e:
        print(f"Decryption failed: {e}")
    
    # Test with legacy Fernet for comparison
    try:
        from cryptography.fernet import Fernet
        import base64
        import hashlib
        from app.core.config import get_settings
        
        settings = get_settings()
        key = hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
        fernet = Fernet(base64.urlsafe_b64encode(key))
        
        fernet_encrypted = fernet.encrypt(test_data.encode()).decode()
        print(f"\nFernet encrypted: {fernet_encrypted}")
        print(f"Fernet starts with 'gAAAAA': {fernet_encrypted.startswith('gAAAAA')}")
        
        fernet_decrypted = fernet.decrypt(fernet_encrypted.encode()).decode()
        print(f"Fernet decrypted: {fernet_decrypted}")
        
    except Exception as e:
        print(f"Fernet test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())