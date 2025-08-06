#!/usr/bin/env python3
"""
Seed Initial Data for Healthcare Platform

Creates admin users, test patients, retention policies, and other
initial data needed for dashboard functionality.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import secrets

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.database_unified import User, Patient, AuditLog
from app.core.security import security_manager
from app.modules.auth.service import auth_service
import structlog

logger = structlog.get_logger()

# Demo data configuration
ADMIN_USERS = [
    {
        "email": "admin@healthcare.local",
        "username": "admin",
        "password": "HealthcareAdmin123!",
        "role": "admin",
        "is_system_user": False
    },
    {
        "email": "operator@healthcare.local", 
        "username": "operator",
        "password": "HealthcareOp123!",
        "role": "operator",
        "is_system_user": False
    },
    {
        "email": "viewer@healthcare.local",
        "username": "viewer", 
        "password": "HealthcareView123!",
        "role": "viewer",
        "is_system_user": False
    },
    {
        "email": "system@healthcare.local",
        "username": "system",
        "password": "HealthcareSys123!",
        "role": "admin",
        "is_system_user": True
    }
]

DEMO_PATIENTS = [
    {
        "mrn": "MRN001234",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-05-15",
        "gender": "male",
        "phone": "+1-555-0101",
        "email": "john.doe@email.com",
        "street_address": "123 Main St",
        "city": "Springfield",
        "state": "IL",
        "zip_code": "62701",
        "consent_status": "active"
    },
    {
        "mrn": "MRN005678",
        "first_name": "Jane",
        "last_name": "Smith",
        "date_of_birth": "1985-08-22",
        "gender": "female", 
        "phone": "+1-555-0102",
        "email": "jane.smith@email.com",
        "street_address": "456 Oak Ave",
        "city": "Springfield",
        "state": "IL",
        "zip_code": "62702",
        "consent_status": "active"
    },
    {
        "mrn": "MRN009876",
        "first_name": "Robert",
        "last_name": "Johnson",
        "date_of_birth": "1978-12-03",
        "gender": "male",
        "phone": "+1-555-0103",
        "email": "robert.johnson@email.com",
        "street_address": "789 Pine Rd",
        "city": "Springfield", 
        "state": "IL",
        "zip_code": "62703",
        "consent_status": "active"
    },
    {
        "mrn": "MRN543210",
        "first_name": "Maria",
        "last_name": "Garcia",
        "date_of_birth": "1992-03-18",
        "gender": "female",
        "phone": "+1-555-0104",
        "email": "maria.garcia@email.com",
        "street_address": "321 Elm St",
        "city": "Springfield",
        "state": "IL", 
        "zip_code": "62704",
        "consent_status": "active"
    },
    {
        "mrn": "MRN987654",
        "first_name": "David",
        "last_name": "Wilson",
        "date_of_birth": "1975-07-09",
        "gender": "male",
        "phone": "+1-555-0105",
        "email": "david.wilson@email.com", 
        "street_address": "654 Maple Dr",
        "city": "Springfield",
        "state": "IL",
        "zip_code": "62705",
        "consent_status": "active"
    }
]

DEMO_AUDIT_EVENTS = [
    {
        "event_type": "USER_LOGIN",
        "action": "login",
        "result": "success",
        "resource_type": "user",
        "ip_address": "192.168.1.100"
    },
    {
        "event_type": "PHI_ACCESS",
        "action": "view_patient",
        "result": "success", 
        "resource_type": "patient",
        "ip_address": "192.168.1.100"
    },
    {
        "event_type": "USER_CREATED",
        "action": "create_user",
        "result": "success",
        "resource_type": "user",
        "ip_address": "192.168.1.101"
    },
    {
        "event_type": "LOGIN_FAILED",
        "action": "login", 
        "result": "failure",
        "resource_type": "user",
        "ip_address": "192.168.1.200"
    },
    {
        "event_type": "AUDIT_LOG_CREATED",
        "action": "create_audit_log",
        "result": "success",
        "resource_type": "audit_log",
        "ip_address": "127.0.0.1"
    }
]

async def create_admin_users():
    """Create admin users for the system."""
    logger.info("Creating admin users")
    
    async for session in get_db():
        try:
            from sqlalchemy import select
            
            created_count = 0
            
            for user_data in ADMIN_USERS:
                # Check if user already exists
                result = await session.execute(
                    select(User).where(User.email == user_data["email"])
                )
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    logger.info("User already exists, skipping", email=user_data["email"])
                    continue
                
                # Create password hash
                password_hash = security_manager.hash_password(user_data["password"])
                
                # Create user
                user = User(
                    email=user_data["email"],
                    username=user_data["username"],
                    password_hash=password_hash,
                    email_verified=True,
                    is_active=True,
                    is_system_user=user_data["is_system_user"],
                    must_change_password=False
                )
                
                session.add(user)
                await session.flush()  # Get the ID
                
                created_count += 1
                logger.info("Created user", 
                          email=user_data["email"],
                          username=user_data["username"],
                          role=user_data["role"],
                          user_id=str(user.id))
            
            await session.commit()
            logger.info("Admin users creation completed", users_created=created_count)
            return created_count
            
        except Exception as e:
            await session.rollback()
            logger.error("Failed to create admin users", error=str(e))
            raise
        finally:
            await session.close()

async def create_demo_patients():
    """Create demo patients for testing."""
    logger.info("Creating demo patients")
    
    async for session in get_db():
        try:
            from sqlalchemy import select
            
            created_count = 0
            
            for patient_data in DEMO_PATIENTS:
                # Check if patient already exists
                result = await session.execute(
                    select(Patient).where(Patient.mrn == security_manager.encrypt_data(patient_data["mrn"]))
                )
                existing_patient = result.scalar_one_or_none()
                
                if existing_patient:
                    logger.info("Patient already exists, skipping", mrn=patient_data["mrn"])
                    continue
                
                # Create patient with encrypted PHI
                patient = Patient(
                    mrn=security_manager.encrypt_data(patient_data["mrn"]),
                    first_name_encrypted=security_manager.encrypt_data(patient_data["first_name"]),
                    last_name_encrypted=security_manager.encrypt_data(patient_data["last_name"]),
                    date_of_birth_encrypted=security_manager.encrypt_data(patient_data["date_of_birth"]),
                    gender_encrypted=security_manager.encrypt_data(patient_data["gender"]),
                    phone_encrypted=security_manager.encrypt_data(patient_data["phone"]),
                    email_encrypted=security_manager.encrypt_data(patient_data["email"]),
                    street_address_encrypted=security_manager.encrypt_data(patient_data["street_address"]),
                    city_encrypted=security_manager.encrypt_data(patient_data["city"]),
                    state_encrypted=security_manager.encrypt_data(patient_data["state"]),
                    zip_code_encrypted=security_manager.encrypt_data(patient_data["zip_code"]),
                    consent_status=patient_data["consent_status"],
                    consent_date=datetime.utcnow(),
                    data_source="demo_seed",
                    fhir_patient_id=f"Patient/{secrets.token_hex(8)}"
                )
                
                session.add(patient)
                created_count += 1
                
                logger.info("Created patient",
                          mrn=patient_data["mrn"],
                          name=f"{patient_data['first_name']} {patient_data['last_name']}")
            
            await session.commit()
            logger.info("Demo patients creation completed", patients_created=created_count)
            return created_count
            
        except Exception as e:
            await session.rollback()
            logger.error("Failed to create demo patients", error=str(e))
            raise
        finally:
            await session.close()

async def create_demo_audit_events():
    """Create demo audit events for dashboard testing."""
    logger.info("Creating demo audit events")
    
    async for session in get_db():
        try:
            created_count = 0
            
            # Create events over the last week for realistic data
            base_time = datetime.utcnow() - timedelta(days=7)
            
            for i, event_data in enumerate(DEMO_AUDIT_EVENTS):
                # Spread events over time
                event_time = base_time + timedelta(
                    days=i % 7,
                    hours=(i * 3) % 24,
                    minutes=(i * 17) % 60
                )
                
                # Get a user for the event
                user_result = await session.execute(
                    select(User).where(User.email == "admin@healthcare.local")
                )
                admin_user = user_result.scalar_one_or_none()
                
                audit_log = AuditLog(
                    timestamp=event_time,
                    event_type=event_data["event_type"],
                    user_id=admin_user.id if admin_user else None,
                    session_id=secrets.token_hex(8),
                    correlation_id=secrets.token_hex(8),
                    resource_type=event_data["resource_type"],
                    resource_id=secrets.token_hex(8),
                    action=event_data["action"],
                    result=event_data["result"],
                    ip_address=event_data["ip_address"],
                    user_agent="Demo-Seed-Script/1.0",
                    request_method="POST",
                    request_path="/api/v1/demo",
                    metadata={"source": "demo_seed", "event_number": i + 1},
                    compliance_tags=["demo", "seed_data"],
                    data_classification="INTERNAL"
                )
                
                session.add(audit_log)
                created_count += 1
            
            # Create additional recent events for "today"
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            for i in range(10):
                event_time = today_start + timedelta(hours=i + 1, minutes=(i * 7) % 60)
                
                audit_log = AuditLog(
                    timestamp=event_time,
                    event_type="PHI_ACCESS",
                    user_id=admin_user.id if admin_user else None,
                    session_id=secrets.token_hex(8),
                    correlation_id=secrets.token_hex(8),
                    resource_type="patient",
                    resource_id=secrets.token_hex(8),
                    action="view_patient_record",
                    result="success",
                    ip_address="192.168.1.100",
                    user_agent="Healthcare-Dashboard/1.0",
                    request_method="GET",
                    request_path=f"/api/v1/healthcare/patients/{secrets.token_hex(8)}",
                    metadata={"source": "demo_seed_today", "event_number": i + 1},
                    compliance_tags=["phi_access", "hipaa"],
                    data_classification="PHI"
                )
                
                session.add(audit_log)
                created_count += 1
            
            await session.commit()
            logger.info("Demo audit events creation completed", events_created=created_count)
            return created_count
            
        except Exception as e:
            await session.rollback()
            logger.error("Failed to create demo audit events", error=str(e))
            raise
        finally:
            await session.close()

async def verify_seeded_data():
    """Verify that data was seeded successfully."""
    logger.info("Verifying seeded data")
    
    async for session in get_db():
        try:
            from sqlalchemy import select, func
            
            # Count users
            user_count = await session.execute(select(func.count(User.id)))
            total_users = user_count.scalar()
            
            # Count patients
            patient_count = await session.execute(select(func.count(Patient.id)))
            total_patients = patient_count.scalar()
            
            # Count audit logs
            audit_count = await session.execute(select(func.count(AuditLog.id)))
            total_audit_logs = audit_count.scalar()
            
            logger.info("Data verification completed",
                       total_users=total_users,
                       total_patients=total_patients,
                       total_audit_logs=total_audit_logs)
            
            # Verify admin user exists
            admin_result = await session.execute(
                select(User).where(User.email == "admin@healthcare.local")
            )
            admin_user = admin_result.scalar_one_or_none()
            
            if admin_user:
                logger.info("Admin user verified",
                          email=admin_user.email,
                          username=admin_user.username,
                          is_active=admin_user.is_active)
            else:
                logger.warning("Admin user not found")
            
            return {
                "users": total_users,
                "patients": total_patients,
                "audit_logs": total_audit_logs,
                "admin_user_exists": admin_user is not None
            }
            
        except Exception as e:
            logger.error("Failed to verify seeded data", error=str(e))
            return None
        finally:
            await session.close()

async def main():
    """Main execution function."""
    try:
        logger.info("Starting initial data seeding")
        
        # Create admin users
        users_created = await create_admin_users()
        
        # Create demo patients
        patients_created = await create_demo_patients()
        
        # Create demo audit events
        events_created = await create_demo_audit_events()
        
        # Verify everything
        verification = await verify_seeded_data()
        
        if verification and verification["admin_user_exists"]:
            logger.info("Initial data seeding completed successfully")
            print("\nInitial data seeding completed!")
            print(f"Users created: {users_created}")
            print(f"Patients created: {patients_created}")
            print(f"Audit events created: {events_created}")
            print(f"\nAdmin login credentials:")
            print(f"Email: admin@healthcare.local")
            print(f"Password: HealthcareAdmin123!")
            print(f"\nDashboard will now show real data instead of placeholders.")
        else:
            logger.error("Initial data seeding failed verification")
            sys.exit(1)
            
    except Exception as e:
        logger.error("Initial data seeding failed", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    # Configure logging
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run seeding
    asyncio.run(main())