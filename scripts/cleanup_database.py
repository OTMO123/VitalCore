#!/usr/bin/env python3
"""
Database cleanup script - removes all data except admin user
"""

import asyncio
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add app to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import get_session_factory
from app.core.database_unified import (
    User, Patient, ClinicalDocument, Consent, PHIAccessLog,
    DocumentStorage, DocumentAccessAudit, DocumentShare, Immunization, 
    IRISApiLog, AuditLog
)
from app.modules.auth.schemas import UserRole
from app.core.security import security_manager
from sqlalchemy import select, delete


async def cleanup_database():
    """Clean database keeping only admin user"""
    print("🧹 Starting database cleanup...")
    
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            # Find admin user
            admin_query = select(User).where(User.username == "admin")
            result = await session.execute(admin_query)
            admin_user = result.scalar_one_or_none()
            
            if not admin_user:
                print("❌ Admin user not found! Creating admin user...")
                
                # Create admin user directly
                hashed_password = security_manager.hash_password("admin123")
                admin_user = User(
                    id=str(uuid.uuid4()),
                    username="admin",
                    email="admin@example.com",
                    password_hash=hashed_password,
                    role=UserRole.ADMIN.value,
                    is_active=True,
                    email_verified=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(admin_user)
                await session.commit()
                await session.refresh(admin_user)
                print(f"✅ Admin user created: {admin_user.username}")
            
            admin_id = admin_user.id
            print(f"📋 Keeping admin user: {admin_user.username} (ID: {admin_id})")
            
            # Clean up tables in order (respecting foreign keys)
            # This order is critical to avoid foreign key constraint violations
            tables_to_clean = [
                # Clean dependent tables first (tables that reference other tables)
                (DocumentShare, "document_shares"),
                (DocumentAccessAudit, "document_access_audit"),
                (DocumentStorage, "document_storage"),
                
                # Clean PHI and healthcare tables that reference users and patients
                (PHIAccessLog, "phi_access_logs"),
                (ClinicalDocument, "clinical_documents"),
                (Immunization, "immunizations"),
                
                # Clean consents AFTER cleaning tables that might reference them
                # but BEFORE cleaning patients/users they reference
                (Consent, "consents"),
                
                # Clean patients AFTER everything that references them
                (Patient, "patients"),
                
                # Clean API logs
                (IRISApiLog, "iris_api_logs"),
                
                # Clean audit logs (but keep admin-related) - BEFORE cleaning users they reference
                (AuditLog, "audit_logs"),
            ]
            
            total_deleted = 0
            
            for model_class, table_name in tables_to_clean:
                try:
                    if table_name == "audit_logs":
                        # Keep audit logs related to admin user
                        delete_stmt = delete(model_class).where(
                            model_class.user_id != admin_id
                        )
                    elif table_name == "phi_access_logs":
                        # Clean PHI access logs for non-admin users
                        delete_stmt = delete(model_class).where(
                            model_class.user_id != admin_id
                        )
                    elif table_name == "consents":
                        # Clean consents NOT granted by admin user
                        delete_stmt = delete(model_class).where(
                            model_class.granted_by != admin_id
                        )
                    else:
                        # Delete all records from other tables
                        delete_stmt = delete(model_class)
                    
                    result = await session.execute(delete_stmt)
                    deleted_count = result.rowcount
                    total_deleted += deleted_count
                    print(f"🗑️  Deleted {deleted_count} records from {table_name}")
                    
                except Exception as e:
                    print(f"⚠️  Warning: Could not clean {table_name}: {e}")
                    # Continue with other tables
                    continue
            
            # Final step: Clean up non-admin users AFTER all dependent records are gone
            try:
                delete_users_stmt = delete(User).where(User.id != admin_id)
                result = await session.execute(delete_users_stmt)
                deleted_users = result.rowcount
                total_deleted += deleted_users
                print(f"🗑️  Deleted {deleted_users} non-admin users")
            except Exception as e:
                print(f"❌ Error deleting users: {e}")
                # Try to identify remaining foreign key references
                print("🔍 Checking for remaining foreign key references...")
                
                # Check for remaining consents that reference users
                remaining_consents = await session.execute(
                    select(Consent).where(Consent.granted_by != admin_id)
                )
                consent_count = len(remaining_consents.all())
                if consent_count > 0:
                    print(f"⚠️  {consent_count} consents still reference users")
                
                # Re-raise the error for proper handling
                raise
            
            await session.commit()
            
            print(f"\n✅ Database cleanup completed!")
            print(f"📊 Total records deleted: {total_deleted}")
            print(f"👤 Admin user preserved: {admin_user.username}")
            print("🔒 Admin credentials: admin / admin123")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error during cleanup: {e}")
            raise


async def verify_cleanup():
    """Verify cleanup was successful"""
    print("\n🔍 Verifying cleanup...")
    
    session_factory = get_session_factory()
    async with session_factory() as session:
        # Count remaining users
        user_count_result = await session.execute(select(User))
        user_count = len(user_count_result.all())
        
        # Count remaining patients
        patient_count_result = await session.execute(select(Patient))
        patient_count = len(patient_count_result.all())
        
        # Count remaining documents
        doc_count_result = await session.execute(select(DocumentStorage))
        doc_count = len(doc_count_result.all())
        
        print(f"📊 Remaining records:")
        print(f"   Users: {user_count} (should be 1 - admin only)")
        print(f"   Patients: {patient_count} (should be 0)")
        print(f"   Documents: {doc_count} (should be 0)")
        
        if user_count == 1 and patient_count == 0 and doc_count == 0:
            print("✅ Cleanup verification successful!")
        else:
            print("⚠️  Cleanup may not be complete")


if __name__ == "__main__":
    print("🚀 Healthcare AI Platform - Database Cleanup")
    print("=" * 50)
    
    # Run cleanup
    asyncio.run(cleanup_database())
    
    # Verify results
    asyncio.run(verify_cleanup())
    
    print("\n🎉 Database cleanup complete!")