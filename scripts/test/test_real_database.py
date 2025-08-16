#!/usr/bin/env python3
"""
REAL Database Test - Actually tests database operations with encryption
"""
import asyncio
import sys
import os
import uuid
from datetime import datetime
sys.path.insert(0, os.getcwd())

async def test_real_database():
    """Test REAL database operations with encryption - not mocks."""
    print("Testing REAL Database Operations...")
    
    try:
        # Import REAL database and models
        from app.core.database_unified import get_session_factory, Patient
        from app.core.security import EncryptionService
        
        encryption = EncryptionService()
        
        print("   Connecting to database...")
        
        # Get session factory and create session
        session_factory = await get_session_factory()
        async with session_factory() as session:
            # Generate unique test data
            test_mrn = f'REAL-TEST-{uuid.uuid4().hex[:8]}'
            test_first_name = f'TestPatient{uuid.uuid4().hex[:4]}'
            test_last_name = f'RealTest{uuid.uuid4().hex[:4]}'
            test_ssn = f'999-{uuid.uuid4().hex[:2]}-{uuid.uuid4().hex[:4]}'
            
            print(f"   Creating patient with MRN: {test_mrn}")
            
            # REAL encryption of PHI
            encrypted_first_name = await encryption.encrypt(test_first_name)
            encrypted_last_name = await encryption.encrypt(test_last_name)
            encrypted_ssn = await encryption.encrypt(test_ssn)
            encrypted_dob = await encryption.encrypt('1990-01-01')
            
            # CRITICAL: Verify encryption actually happened
            if encrypted_first_name == test_first_name:
                print("   FAILED: First name not encrypted!")
                return False
            
            if encrypted_ssn == test_ssn:
                print("   FAILED: SSN not encrypted!")
                return False
            
            # Create REAL Patient model with correct field names
            patient = Patient(
                first_name_encrypted=encrypted_first_name,
                last_name_encrypted=encrypted_last_name,
                date_of_birth_encrypted=encrypted_dob,
                ssn_encrypted=encrypted_ssn,
                mrn=test_mrn,
                gender='other'
            )
            
            # REAL database INSERT
            session.add(patient)
            await session.commit()
            await session.refresh(patient)
            
            patient_id = patient.id
            print(f"   Patient created in database with ID: {patient_id}")
            
            # CRITICAL: Verify patient was actually saved
            if patient_id is None:
                print("   FAILED: Patient ID is None - not saved!")
                return False
            
            # REAL database SELECT
            from sqlalchemy import select
            stmt = select(Patient).where(Patient.id == patient_id)
            result = await session.execute(stmt)
            stored_patient = result.scalar_one_or_none()
            
            # CRITICAL: Verify patient was found
            if stored_patient is None:
                print("   FAILED: Patient not found in database!")
                return False
            
            # CRITICAL: Verify data is encrypted in database
            if stored_patient.first_name_encrypted == test_first_name:
                print("   FAILED: First name stored unencrypted!")
                return False
            
            # REAL decryption of stored data
            decrypted_first = await encryption.decrypt(stored_patient.first_name_encrypted)
            decrypted_last = await encryption.decrypt(stored_patient.last_name_encrypted)
            decrypted_ssn = await encryption.decrypt(stored_patient.ssn_encrypted)
            decrypted_dob = await encryption.decrypt(stored_patient.date_of_birth_encrypted)
            
            # CRITICAL: Verify decryption matches original data
            if decrypted_first != test_first_name:
                print(f"   FAILED: First name mismatch: {decrypted_first} != {test_first_name}")
                return False
            
            if decrypted_last != test_last_name:
                print(f"   FAILED: Last name mismatch: {decrypted_last} != {test_last_name}")
                return False
            
            if decrypted_ssn != test_ssn:
                print(f"   FAILED: SSN mismatch: {decrypted_ssn} != {test_ssn}")
                return False
                
            if decrypted_dob != '1990-01-01':
                print(f"   FAILED: DOB mismatch: {decrypted_dob} != 1990-01-01")
                return False
            
            print("   Database encryption/decryption cycle VERIFIED")
            print(f"      Original: {test_first_name} / {test_ssn}")
            print(f"      Stored encrypted, retrieved and decrypted correctly")
            
            # REAL database DELETE (cleanup)
            await session.delete(stored_patient)
            await session.commit()
            
            # CRITICAL: Verify deletion worked
            stmt = select(Patient).where(Patient.id == patient_id)
            result = await session.execute(stmt)
            deleted_patient = result.scalar_one_or_none()
            
            if deleted_patient is not None:
                print("   FAILED: Patient not deleted from database!")
                return False
            
            print("   Test data cleaned up successfully")
            
        return True
        
    except ImportError as e:
        print(f"   IMPORT FAILED: {e}")
        print("   This means database/encryption services are not available")
        return False
    except Exception as e:
        print(f"   DATABASE TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_real_database())
    print(f"\nFinal Result: {'PASSED' if result else 'FAILED'}")
    sys.exit(0 if result else 1)