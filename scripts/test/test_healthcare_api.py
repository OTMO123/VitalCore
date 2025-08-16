#!/usr/bin/env python3
"""
Test healthcare API directly to see the error
"""

import asyncio
import sys
sys.path.append('/mnt/c/Users/aurik/Code_Projects/2_scraper')

from app.modules.healthcare_records.service import get_healthcare_service
from app.core.database_unified import get_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_healthcare_api():
    """Test healthcare service directly"""
    
    print("TESTING HEALTHCARE API")
    print("=" * 50)
    
    try:
        async for session in get_db():
            # Test healthcare service
            service = await get_healthcare_service(session=session)
            
            # Test search_patients method
            from app.modules.healthcare_records.service import AccessContext
            context = AccessContext(
                user_id="test-user",
                purpose="operations", 
                role="ADMIN",
                ip_address=None,
                session_id=None
            )
            
            patients, total_count = await service.patient_service.search_patients(
                context=context,
                filters=None,
                limit=20,
                offset=0
            )
            
            print(f"Patients retrieved: {len(patients)} (total: {total_count})")
            for patient in patients:
                print(f"  - ID: {patient.id}")
                print(f"    MRN: {patient.mrn}")
                print(f"    External ID: {patient.external_id}")
                print(f"    Classification: {patient.data_classification}")
            
            return True
            
            break
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_healthcare_api())
    sys.exit(0 if result else 1)