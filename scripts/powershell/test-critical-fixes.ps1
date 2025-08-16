#!/usr/bin/env pwsh

Write-Host "Testing Critical Error Fixes..." -ForegroundColor Cyan

Write-Host "1. Testing UserRole enum with legacy compatibility..." -ForegroundColor Yellow
docker-compose exec app python -c "
from app.modules.auth.schemas import UserRole
print('Legacy USER role:', UserRole.USER)
print('Legacy ADMIN role:', UserRole.ADMIN)
print('New PHYSICIAN role:', UserRole.PHYSICIAN)
print('Total roles:', len([r.value for r in UserRole]))
"

Write-Host "2. Testing encryption service..." -ForegroundColor Yellow  
docker-compose exec app python -c "
import asyncio
async def test_encryption():
    from app.core.security import EncryptionService
    service = EncryptionService()
    test_data = 'test-phi-data'
    encrypted = await service.encrypt(test_data)
    decrypted = await service.decrypt(encrypted)
    print('Encryption test:', 'PASS' if decrypted == test_data else 'FAIL')
asyncio.run(test_encryption())
"

Write-Host "3. Testing audit service..." -ForegroundColor Yellow
docker-compose exec app python -c "
import asyncio
from app.modules.audit_logger.service import SOC2AuditService

async def test_audit():
    from app.core.database_unified import async_sessionmaker, engine
    session_factory = async_sessionmaker(engine)
    service = SOC2AuditService(session_factory)
    
    try:
        log = await service.log_action(
            user_id='test-user',
            action='test-action',
            resource_type='test',
            resource_id='123'
        )
        print('Audit service test:', 'PASS' if log else 'FAIL')
    except Exception as e:
        print('Audit service test: FAIL -', str(e))

try:
    asyncio.run(test_audit())
except Exception as e:
    print('Audit test error:', e)
"

Write-Host "4. Testing health endpoints..." -ForegroundColor Yellow
docker-compose exec app python -c "
import asyncio
async def test_health():
    import httpx
    from app.main import app
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as client:
        # Basic health
        response = await client.get('/health')
        basic_ok = response.status_code == 200 and 'timestamp' in response.json()
        print('Basic health endpoint:', 'PASS' if basic_ok else 'FAIL')
        
        # Detailed health
        response = await client.get('/health/detailed')
        detailed_ok = response.status_code == 200 and 'components' in response.json()
        print('Detailed health endpoint:', 'PASS' if detailed_ok else 'FAIL')

try:
    asyncio.run(test_health())
except Exception as e:
    print('Health test error:', e)
"

Write-Host "5. Running key smoke tests..." -ForegroundColor Yellow
docker-compose exec app pytest app/tests/smoke/test_system_startup.py::TestSystemStartup::test_encryption_service_initialization -v

Write-Host "Critical Fixes Test Complete!" -ForegroundColor Green