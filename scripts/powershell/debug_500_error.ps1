# Debug the exact 500 error with full traceback
Write-Host "Getting full error traceback from Patient API..." -ForegroundColor Yellow

# Enable debug logging in container
docker exec -it iris_app bash -c 'export PYTHONPATH=/app && python3 -c "
import asyncio
import sys
import traceback
sys.path.append(\"/app\")

async def debug_patient_api():
    try:
        from app.modules.healthcare_records.service import get_healthcare_service, AccessContext
        from app.core.database_advanced import get_db
        
        # Get database session
        db_gen = get_db()
        db = await db_gen.__anext__()
        
        # Get healthcare service
        service = await get_healthcare_service(session=db)
        
        # Create access context
        context = AccessContext(
            user_id=\"admin\",
            purpose=\"operations\",
            role=\"admin\", 
            ip_address=\"127.0.0.1\",
            session_id=\"debug\"
        )
        
        print(\"🔍 Starting patient search debug...\")
        
        # This is where it fails - let's catch the exact error
        patients, count = await service.patient_service.search_patients(context)
        
        print(f\"✅ Success: Found {count} patients\")
        
        await db.close()
        
    except Exception as e:
        print(f\"❌ EXACT ERROR: {e}\")
        print(f\"❌ ERROR TYPE: {type(e).__name__}\")
        print(\"❌ FULL TRACEBACK:\")
        traceback.print_exc()

asyncio.run(debug_patient_api())
"'

Write-Host "Error investigation completed." -ForegroundColor Green