#!/usr/bin/env python3
"""
Simple patient creation test that bypasses the complex service layer
"""

import asyncio
import sys
import os
sys.path.append('/mnt/c/Users/aurik/Code_Projects/2_scraper')

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database_unified import get_db, Patient, DataClassification
from app.core.security import SecurityManager

async def test_simple_patient_creation():
    """Test creating a patient directly with the database"""
    print("🧪 Testing simple patient creation...")
    
    try:
        # Get database session
        async for session in get_db():
            # Create security manager for encryption
            security_manager = SecurityManager()
            
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            
            # Create a simple patient with explicit lowercase enum value
            patient = Patient(
                external_id=f"TEST{unique_id}",
                mrn=f"P{unique_id}-TEST", 
                first_name_encrypted=security_manager.encrypt_data("Test"),
                last_name_encrypted=security_manager.encrypt_data("Patient"),
                date_of_birth_encrypted=security_manager.encrypt_data("1990-01-01"),
                data_classification="phi",  # Use string value directly
                consent_status={"status": "active", "types": ["treatment"]}
            )
            
            # Add to session
            session.add(patient)
            await session.commit()
            
            print(f"✅ Patient created successfully with ID: {patient.id}")
            return True
            
    except Exception as e:
        print(f"❌ Failed to create patient: {e}")
        return False

async def main():
    success = await test_simple_patient_creation()
    return 0 if success else 1

if __name__ == "__main__":
    asyncio.run(main())