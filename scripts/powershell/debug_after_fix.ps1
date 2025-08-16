# Debug what error happens now after PatientFilters fix
Write-Host "Debugging error after PatientFilters fix..." -ForegroundColor Yellow

docker exec -it iris_app python3 -c "
import asyncio
import sys
import traceback
sys.path.append('/app')

async def debug_after_fix():
    try:
        from app.modules.healthcare_records.router import list_patients
        from app.core.database_advanced import get_db
        
        db_gen = get_db()
        db = await db_gen.__anext__()
        
        user_id = 'admin'
        user_info = {'role': 'admin', 'username': 'admin'}
        
        print('Testing HTTP router after PatientFilters fix...')
        
        result = await list_patients(
            page=1,
            size=20, 
            search=None,
            gender=None,
            age_min=None,
            age_max=None,
            department_id=None,
            current_user_id=user_id,
            db=db,
            user_info=user_info
        )
        
        print(f'SUCCESS: {result}')
        
        await db.close()
        
    except Exception as e:
        print(f'NEW ERROR: {e}')
        print(f'ERROR TYPE: {type(e).__name__}')
        print('FULL TRACEBACK:')
        traceback.print_exc()

asyncio.run(debug_after_fix())
"

Write-Host "Debug completed" -ForegroundColor Green