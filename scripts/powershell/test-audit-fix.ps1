#!/usr/bin/env pwsh

Write-Host "Testing AuditEvent Validation Fixes" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

Write-Host "`nTesting AuditEvent creation with required fields..." -ForegroundColor Yellow

# Test if we can create an AuditEvent with all required fields
docker-compose exec app python -c "
from app.modules.audit_logger.schemas import AuditEvent, SOC2Category
from datetime import datetime
from uuid import uuid4

try:
    # Test creating an AuditEvent with all required fields
    event = AuditEvent(
        event_id=str(uuid4()),
        timestamp=datetime.utcnow(),
        event_type='test-action',
        aggregate_id='test-user',      # Required by BaseEvent
        aggregate_type='audit_log',    # Required by BaseEvent
        publisher='audit_service',     # Required by BaseEvent
        user_id='test-user',
        operation='test-action',
        outcome='success',             # Required by AuditEvent
        resource_type='test',
        resource_id='123',
        headers={},
        compliance_tags=['soc2', 'test'],
        data_classification='internal',
        soc2_category=SOC2Category.SECURITY  # Use enum, not string
    )
    print('✅ AuditEvent validation: PASS')
    print('   Event ID:', event.event_id)
    print('   Event Type:', event.event_type)
    print('   SOC2 Category:', event.soc2_category)
    print('   Aggregate ID:', event.aggregate_id)
    print('   Aggregate Type:', event.aggregate_type)
    print('   Publisher:', event.publisher)
    print('   Outcome:', event.outcome)
    
except Exception as e:
    print('❌ AuditEvent validation: FAIL')
    print('   Error:', str(e))
    print('   Error type:', type(e).__name__)
"

Write-Host "`nTesting SOC2AuditService log_action method..." -ForegroundColor Yellow

docker-compose exec app python -c "
import asyncio
from app.modules.audit_logger.service import SOC2AuditService

async def test_audit_service():
    try:
        from app.core.database_unified import async_sessionmaker, engine
        session_factory = async_sessionmaker(engine)
        service = SOC2AuditService(session_factory)
        
        # Test the log_action method with fixed validation
        log = await service.log_action(
            user_id='test-user',
            action='test-action',
            resource_type='test',
            resource_id='123'
        )
        
        if log:
            print('✅ SOC2AuditService log_action: PASS')
            print('   Log ID:', getattr(log, 'id', 'N/A'))
            print('   User ID:', getattr(log, 'user_id', 'N/A'))
            print('   Action:', getattr(log, 'action', 'N/A'))
        else:
            print('❌ SOC2AuditService log_action: FAIL - No log returned')
            
    except Exception as e:
        print('❌ SOC2AuditService log_action: FAIL')
        print('   Error:', str(e))
        print('   Error type:', type(e).__name__)
        import traceback
        print('   Traceback:', traceback.format_exc())

asyncio.run(test_audit_service())
"

Write-Host "`n📈 Summary of AuditEvent Fixes Applied:" -ForegroundColor Green
Write-Host "✅ Fixed SOC2Category enum usage (was string, now enum)" -ForegroundColor Green
Write-Host "✅ Added required aggregate_id field to AuditEvent creation" -ForegroundColor Green
Write-Host "✅ Added required aggregate_type field to AuditEvent creation" -ForegroundColor Green
Write-Host "✅ Publisher field already provided" -ForegroundColor Green
Write-Host "✅ Outcome field already provided" -ForegroundColor Green

Write-Host "`n🎯 Next: Run the smoke tests to verify all fixes:" -ForegroundColor Cyan
Write-Host "   .\test-userrole-system.ps1" -ForegroundColor White

Write-Host "`nAuditEvent Validation Fixes Complete!" -ForegroundColor Green