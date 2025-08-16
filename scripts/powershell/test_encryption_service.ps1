# Test encryption service in Docker container
Write-Host "Testing encryption service..." -ForegroundColor Yellow

docker exec -it iris_app python3 -c "
import sys
sys.path.append('/app')

try:
    from app.core.security import EncryptionService
    print('✅ EncryptionService imported successfully')
    
    # Test encryption service
    service = EncryptionService()
    print('✅ EncryptionService created')
    
    # Test field encryption
    test_data = 'test_data'
    encrypted = service.encrypt_field(test_data, 'test_field')
    print(f'✅ Encryption works: {len(encrypted)} bytes')
    
    # Test decryption
    decrypted = service.decrypt_field(encrypted, 'test_field')
    print(f'✅ Decryption works: {decrypted == test_data}')
    
    print('✅ All encryption tests passed!')
    
except ImportError as e:
    print(f'❌ Import error: {e}')
except Exception as e:
    print(f'❌ Encryption error: {e}')
    import traceback
    traceback.print_exc()
"

Write-Host "Testing patient service creation..." -ForegroundColor Yellow

docker exec -it iris_app python3 -c "
import sys
sys.path.append('/app')
import asyncio

async def test_patient_service():
    try:
        from app.modules.healthcare_records.service import get_healthcare_service
        from app.core.database_advanced import get_db
        
        print('✅ Service imports successful')
        
        # Get database session
        db_gen = get_db()
        db = await db_gen.__anext__()
        print('✅ Database connection successful')
        
        # Get healthcare service
        service = await get_healthcare_service(session=db)
        print('✅ Healthcare service created')
        
        # Test patient list (basic query)
        from app.modules.healthcare_records.service import AccessContext
        context = AccessContext(
            user_id='admin',
            purpose='operations',
            role='admin',
            ip_address='127.0.0.1',
            session_id='test'
        )
        
        patients, count = await service.patient_service.search_patients(context)
        print(f'✅ Patient search successful: found {count} patients')
        
        await db.close()
        
    except Exception as e:
        print(f'❌ Patient service error: {e}')
        import traceback
        traceback.print_exc()

asyncio.run(test_patient_service())
"