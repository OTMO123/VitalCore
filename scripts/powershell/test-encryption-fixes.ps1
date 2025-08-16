#!/usr/bin/env pwsh

Write-Host "Testing Encryption Service Fixes..." -ForegroundColor Cyan

Write-Host "1. Testing async encryption methods..." -ForegroundColor Yellow
docker-compose exec app python -c "
import asyncio
async def test_async_encryption():
    from app.core.security import EncryptionService
    service = EncryptionService()
    test_data = 'test-phi-data'
    
    try:
        encrypted = await service.encrypt(test_data)
        decrypted = await service.decrypt(encrypted)
        result = decrypted == test_data
        print('Async encryption test:', 'PASS' if result else 'FAIL')
        print('Encrypted length:', len(encrypted))
        print('Original data:', test_data)
        print('Decrypted data:', decrypted)
    except Exception as e:
        print('Async encryption test: FAIL -', str(e))

asyncio.run(test_async_encryption())
"

Write-Host "2. Testing sync encryption methods..." -ForegroundColor Yellow  
docker-compose exec app python -c "
from app.core.security import EncryptionService
service = EncryptionService()
test_data = 'test-phi-data'

try:
    encrypted = service.encrypt_sync(test_data)
    decrypted = service.decrypt_sync(encrypted)
    result = decrypted == test_data
    print('Sync encryption test:', 'PASS' if result else 'FAIL')
    print('Encrypted length:', len(encrypted))
    print('Original data:', test_data)
    print('Decrypted data:', decrypted)
except Exception as e:
    print('Sync encryption test: FAIL -', str(e))
"

Write-Host "3. Testing bulk encryption methods..." -ForegroundColor Yellow
docker-compose exec app python -c "
import asyncio
async def test_bulk_encryption():
    from app.core.security import EncryptionService
    service = EncryptionService()
    test_data_list = ['test-data-1', 'test-data-2', 'test-data-3']
    
    try:
        # Test async bulk methods
        encrypted_list = await service.bulk_encrypt(test_data_list)
        decrypted_list = await service.bulk_decrypt(encrypted_list)
        async_result = decrypted_list == test_data_list
        print('Async bulk encryption test:', 'PASS' if async_result else 'FAIL')
        
        # Test sync bulk methods
        encrypted_list_sync = service.bulk_encrypt_sync(test_data_list)
        decrypted_list_sync = service.bulk_decrypt_sync(encrypted_list_sync)
        sync_result = decrypted_list_sync == test_data_list
        print('Sync bulk encryption test:', 'PASS' if sync_result else 'FAIL')
        
    except Exception as e:
        print('Bulk encryption test: FAIL -', str(e))

asyncio.run(test_bulk_encryption())
"

Write-Host "4. Testing compatibility with existing tests..." -ForegroundColor Yellow
docker-compose exec app pytest app/tests/smoke/test_system_startup.py::TestSystemStartup::test_encryption_service_initialization -v

Write-Host "Encryption Service Fixes Test Complete!" -ForegroundColor Green