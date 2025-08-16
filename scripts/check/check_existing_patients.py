#!/usr/bin/env python3
"""
Check existing patients in database and decrypt their data
"""

import asyncio
import sys
sys.path.append('/mnt/c/Users/aurik/Code_Projects/2_scraper')

from app.core.database_unified import get_db, Patient
from app.core.security import SecurityManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_existing_patients():
    """Check what patients we already have"""
    
    print("CHECKING EXISTING PATIENTS")
    print("=" * 50)
    
    try:
        async for session in get_db():
            # Query all patients
            from sqlalchemy import select
            result = await session.execute(select(Patient))
            patients = result.scalars().all()
            
            print(f"Found {len(patients)} patients in database:")
            
            if patients:
                security_manager = SecurityManager()
                
                for i, patient in enumerate(patients, 1):
                    print(f"\nPatient {i}:")
                    print(f"  ID: {patient.id}")
                    print(f"  External ID: {patient.external_id}")
                    print(f"  MRN: {patient.mrn}")
                    print(f"  Created: {patient.created_at}")
                    
                    # Decrypt sensitive data
                    try:
                        first_name = security_manager.decrypt_data(patient.first_name_encrypted)
                        last_name = security_manager.decrypt_data(patient.last_name_encrypted)
                        birth_date = security_manager.decrypt_data(patient.date_of_birth_encrypted)
                        
                        print(f"  Name: {first_name} {last_name}")
                        print(f"  Birth Date: {birth_date}")
                        print(f"  Data Classification: {patient.data_classification}")
                        print(f"  Consent Status: {patient.consent_status}")
                        
                    except Exception as e:
                        print(f"  Decryption error: {e}")
            else:
                print("No patients found in database")
            
            break
        
        return len(patients) > 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

async def main():
    has_patients = await check_existing_patients()
    
    if has_patients:
        print("\n✅ Database has patient data")
        print("Your frontend should now display real patients!")
        print("Navigate to: http://localhost:3000/patients")
        return 0
    else:
        print("\n❌ No patients found")
        return 1

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)