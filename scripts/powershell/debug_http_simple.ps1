# Debug HTTP layer for patient endpoint
Write-Host "Debugging HTTP layer..." -ForegroundColor Yellow

docker exec -it iris_app python3 -c "
import asyncio
import sys
import traceback
sys.path.append('/app')

async def debug_http_router():
    try:
        from app.modules.healthcare_records.router import list_patients
        from app.core.database_advanced import get_db
        
        db_gen = get_db()
        db = await db_gen.__anext__()
        
        user_id = 'admin'
        user_info = {'role': 'admin', 'username': 'admin'}
        
        print('Testing HTTP router function directly...')
        
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
        
        print(f'HTTP router SUCCESS: {result}')
        
        await db.close()
        
    except Exception as e:
        print(f'HTTP ROUTER ERROR: {e}')
        print(f'ERROR TYPE: {type(e).__name__}')
        print('FULL TRACEBACK:')
        traceback.print_exc()

asyncio.run(debug_http_router())
"

Write-Host "HTTP debug completed" -ForegroundColor Green