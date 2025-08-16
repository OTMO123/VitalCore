#!/usr/bin/env python3
"""
Populate test data for frontend testing
Creates users and patients for testing the frontend interface
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import sys
from pathlib import Path

# Add app to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import get_async_session
from app.core.database_unified import User, Patient, Organization
from app.core.security import security_manager

async def create_test_users():
    """Create test users with different roles"""
    async with get_async_session() as session:
        try:
            # Check if users already exist
            existing_users = await session.execute(
                "SELECT COUNT(*) FROM users"
            )
            user_count = existing_users.scalar()
            
            if user_count > 0:
                print(f"✓ Found {user_count} existing users, skipping user creation")
                return
            
            users_data = [
                {
                    "username": "admin",
                    "email": "admin@healthcare.local",
                    "password": "admin123",
                    "role": "admin",
                    "full_name": "System Administrator"
                },
                {
                    "username": "doctor1",
                    "email": "doctor1@healthcare.local",
                    "password": "doctor123",
                    "role": "doctor",
                    "full_name": "Dr. John Smith"
                },
                {
                    "username": "nurse1",
                    "email": "nurse1@healthcare.local",
                    "password": "nurse123",
                    "role": "nurse",
                    "full_name": "Nurse Jane Wilson"
                },
                {
                    "username": "operator1",
                    "email": "operator1@healthcare.local",
                    "password": "operator123",
                    "role": "operator",
                    "full_name": "Medical Operator Sarah Brown"
                }
            ]
            
            created_users = []
            for user_data in users_data:
                # Hash password
                hashed_password = security_manager.hash_password(user_data["password"])
                
                user = User(
                    id=str(uuid.uuid4()),
                    username=user_data["username"],
                    email=user_data["email"],
                    password_hash=hashed_password,
                    role=user_data["role"],
                    full_name=user_data["full_name"],
                    is_active=True,
                    email_verified=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                session.add(user)
                created_users.append(user)
                print(f"✓ Created user: {user.username} ({user.role})")
            
            await session.commit()
            print(f"✅ Successfully created {len(created_users)} test users")
            
            # Print login credentials
            print("\n📋 LOGIN CREDENTIALS:")
            print("-" * 50)
            for user_data in users_data:
                print(f"Username: {user_data['username']}")
                print(f"Password: {user_data['password']}")
                print(f"Role: {user_data['role']}")
                print("-" * 30)
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Failed to create users: {e}")
            raise

async def create_test_organization():
    """Create test organization"""
    async with get_async_session() as session:
        try:
            # Check if organization exists
            existing_org = await session.execute(
                "SELECT COUNT(*) FROM organizations"
            )
            org_count = existing_org.scalar()
            
            if org_count > 0:
                print("✓ Organization already exists, skipping")
                return
            
            org = Organization(
                id=str(uuid.uuid4()),
                name="Test Healthcare Center",
                type="hospital",
                identifier="THC-001",
                address="123 Healthcare Street, Medical City, MC 12345",
                phone="+1-555-0123",
                email="contact@testhealthcare.local",
                website="https://testhealthcare.local",
                status="active",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(org)
            await session.commit()
            print("✅ Created test organization")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Failed to create organization: {e}")
            raise

async def create_test_patients():
    """Create test patients for frontend testing"""
    async with get_async_session() as session:
        try:
            # Check if patients already exist
            existing_patients = await session.execute(
                "SELECT COUNT(*) FROM patients"
            )
            patient_count = existing_patients.scalar()
            
            if patient_count > 0:
                print(f"✓ Found {patient_count} existing patients, skipping patient creation")
                return
            
            # Get organization ID
            org_result = await session.execute(
                "SELECT id FROM organizations LIMIT 1"
            )
            org_id = org_result.scalar()
            
            if not org_id:
                print("❌ No organization found, creating one first...")
                await create_test_organization()
                org_result = await session.execute(
                    "SELECT id FROM organizations LIMIT 1"
                )
                org_id = org_result.scalar()
            
            patients_data = [
                {
                    "identifier": "P001-2024",
                    "family_name": "Johnson",
                    "given_names": ["Alice", "Marie"],
                    "birth_date": "1985-06-15",
                    "gender": "female",
                    "phone": "+1-555-0101",
                    "email": "alice.johnson@email.com",
                    "address": "123 Main Street, Springfield, IL 62701",
                    "emergency_contact": "Robert Johnson (+1-555-0102)"
                },
                {
                    "identifier": "P002-2024",
                    "family_name": "Smith",
                    "given_names": ["Robert", "James"],
                    "birth_date": "1978-11-22",
                    "gender": "male",
                    "phone": "+1-555-0201",
                    "email": "robert.smith@email.com",
                    "address": "456 Oak Avenue, Springfield, IL 62702",
                    "emergency_contact": "Mary Smith (+1-555-0202)"
                },
                {
                    "identifier": "P003-2024",
                    "family_name": "Williams",
                    "given_names": ["Emily", "Rose"],
                    "birth_date": "1992-03-08",
                    "gender": "female",
                    "phone": "+1-555-0301",
                    "email": "emily.williams@email.com",
                    "address": "789 Pine Street, Springfield, IL 62703",
                    "emergency_contact": "David Williams (+1-555-0302)"
                },
                {
                    "identifier": "P004-2024",
                    "family_name": "Brown",
                    "given_names": ["Michael", "Andrew"],
                    "birth_date": "1965-09-14",
                    "gender": "male",
                    "phone": "+1-555-0401",
                    "email": "michael.brown@email.com",
                    "address": "321 Elm Drive, Springfield, IL 62704",
                    "emergency_contact": "Susan Brown (+1-555-0402)"
                },
                {
                    "identifier": "P005-2024",
                    "family_name": "Davis",
                    "given_names": ["Sarah", "Elizabeth"],
                    "birth_date": "1990-12-03",
                    "gender": "female",
                    "phone": "+1-555-0501",
                    "email": "sarah.davis@email.com",
                    "address": "654 Maple Court, Springfield, IL 62705",
                    "emergency_contact": "John Davis (+1-555-0502)"
                },
                {
                    "identifier": "P006-2024",
                    "family_name": "Wilson",
                    "given_names": ["Thomas", "Edward"],
                    "birth_date": "1972-07-28",
                    "gender": "male",
                    "phone": "+1-555-0601",
                    "email": "thomas.wilson@email.com",
                    "address": "987 Cedar Lane, Springfield, IL 62706",
                    "emergency_contact": "Lisa Wilson (+1-555-0602)"
                },
                {
                    "identifier": "P007-2024",
                    "family_name": "Garcia",
                    "given_names": ["Maria", "Isabel"],
                    "birth_date": "1988-04-19",
                    "gender": "female",
                    "phone": "+1-555-0701",
                    "email": "maria.garcia@email.com",
                    "address": "147 Birch Road, Springfield, IL 62707",
                    "emergency_contact": "Carlos Garcia (+1-555-0702)"
                },
                {
                    "identifier": "P008-2024",
                    "family_name": "Martinez",
                    "given_names": ["Jose", "Luis"],
                    "birth_date": "1983-01-11",
                    "gender": "male",
                    "phone": "+1-555-0801",
                    "email": "jose.martinez@email.com",
                    "address": "258 Spruce Street, Springfield, IL 62708",
                    "emergency_contact": "Ana Martinez (+1-555-0802)"
                }
            ]
            
            created_patients = []
            for patient_data in patients_data:
                # Calculate age
                birth_date = datetime.strptime(patient_data["birth_date"], "%Y-%m-%d").date()
                age = (datetime.now().date() - birth_date).days // 365
                
                # Create FHIR-compliant patient record
                patient = Patient(
                    id=str(uuid.uuid4()),
                    identifier=[{
                        "use": "official",
                        "value": patient_data["identifier"]
                    }],
                    name=[{
                        "family": patient_data["family_name"],
                        "given": patient_data["given_names"],
                        "use": "official"
                    }],
                    active=True,
                    birth_date=patient_data["birth_date"],
                    gender=patient_data["gender"],
                    address=[{
                        "use": "home",
                        "text": patient_data["address"],
                        "line": [patient_data["address"].split(",")[0]],
                        "city": "Springfield",
                        "state": "IL",
                        "country": "US"
                    }],
                    telecom=[
                        {
                            "system": "phone",
                            "value": patient_data["phone"],
                            "use": "mobile"
                        },
                        {
                            "system": "email",
                            "value": patient_data["email"],
                            "use": "home"
                        }
                    ],
                    organization_id=org_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    # Additional fields for the frontend
                    meta={
                        "age": age,
                        "emergency_contact": patient_data["emergency_contact"],
                        "registration_date": datetime.utcnow().isoformat(),
                        "last_visit": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                        "risk_score": round((age / 100) * 0.3 + 0.1, 2),  # Simple risk calculation
                        "consent_status": "active",
                        "phi_protection": "encrypted"
                    }
                )
                
                session.add(patient)
                created_patients.append(patient)
                print(f"✓ Created patient: {patient_data['given_names'][0]} {patient_data['family_name']} (ID: {patient_data['identifier']})")
            
            await session.commit()
            print(f"✅ Successfully created {len(created_patients)} test patients")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Failed to create patients: {e}")
            raise

async def main():
    """Main function to populate all test data"""
    print("🚀 Starting test data population...")
    print("=" * 60)
    
    try:
        # Create test organization first
        print("\n1. Creating test organization...")
        await create_test_organization()
        
        # Create test users
        print("\n2. Creating test users...")
        await create_test_users()
        
        # Create test patients
        print("\n3. Creating test patients...")
        await create_test_patients()
        
        print("\n" + "=" * 60)
        print("🎉 SUCCESS: All test data created successfully!")
        print("\n📝 Next steps:")
        print("1. Start the backend: python app/main.py")
        print("2. Start the frontend: npm run dev")
        print("3. Login with any of the created users")
        print("4. Navigate to the Patients page to see the test data")
        
        print("\n🔑 Quick login (copy to clipboard):")
        print("Username: admin")
        print("Password: admin123")
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)