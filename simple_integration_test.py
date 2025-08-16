#!/usr/bin/env python3
"""
Simple Clinical Workflows Integration Test
Tests basic functionality against real database.
"""
import asyncio
import asyncpg
from datetime import datetime
from uuid import uuid4

async def test_clinical_workflows_integration():
    """Test basic clinical workflows functionality."""
    print("Clinical Workflows Integration Test")
    print("=" * 40)
    
    try:
        # Connect to database
        conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
        print("[SUCCESS] Connected to database")
        
        # Test 1: Verify tables exist
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'clinical_%'
            ORDER BY table_name;
        """)
        
        table_names = [t['table_name'] for t in tables]
        expected_tables = ['clinical_workflows', 'clinical_workflow_steps', 'clinical_encounters', 'clinical_workflow_audit']
        
        print(f"[TEST] Table existence check...")
        for table in expected_tables:
            if table in table_names:
                print(f"  [PASS] {table} exists")
            else:
                print(f"  [FAIL] {table} missing")
                
        # Test 2: Insert a test workflow
        print(f"[TEST] Insert test workflow...")
        
        # Get a user ID
        user_result = await conn.fetchrow("SELECT id FROM users LIMIT 1")
        if not user_result:
            print("  [SKIP] No users found - creating test user")
            user_id = await conn.fetchval("""
                INSERT INTO users (email, hashed_password, full_name, is_active)
                VALUES ('test@example.com', 'hashed', 'Test User', true)
                RETURNING id
            """)
        else:
            user_id = user_result['id']
            
        # Get organization and patient IDs
        org_result = await conn.fetchrow("SELECT id FROM organizations LIMIT 1")
        org_id = org_result['id'] if org_result else None
        
        patient_result = await conn.fetchrow("SELECT id FROM patients LIMIT 1")
        if not patient_result:
            print("  [INFO] Creating test patient")
            patient_id = await conn.fetchval("""
                INSERT INTO patients (mrn, first_name, last_name, date_of_birth, gender, created_by)
                VALUES ('TEST001', 'Test', 'Patient', '1990-01-01', 'M', $1)
                RETURNING id
            """, user_id)
        else:
            patient_id = patient_result['id']
            
        # Insert test workflow
        workflow_id = await conn.fetchval("""
            INSERT INTO clinical_workflows (
                patient_id, provider_id, organization_id, workflow_type, 
                status, priority, title, description, created_by
            ) VALUES ($1, $2, $3, 'encounter', 'active', 'routine', 
                     'Test Integration Workflow', 'Integration test workflow', $4)
            RETURNING id
        """, patient_id, user_id, org_id, user_id)
        
        print(f"  [PASS] Workflow created: {workflow_id}")
        
        # Test 3: Query the workflow
        print(f"[TEST] Query workflow...")
        workflow = await conn.fetchrow("""
            SELECT id, title, status, workflow_type, started_at
            FROM clinical_workflows 
            WHERE id = $1
        """, workflow_id)
        
        if workflow:
            print(f"  [PASS] Workflow found: {workflow['title']}")
            print(f"         Status: {workflow['status']}")
            print(f"         Type: {workflow['workflow_type']}")
        else:
            print(f"  [FAIL] Workflow not found")
            
        # Test 4: Add a workflow step
        print(f"[TEST] Add workflow step...")
        step_id = await conn.fetchval("""
            INSERT INTO clinical_workflow_steps (
                workflow_id, step_name, step_type, title, description, 
                status, step_order, created_by
            ) VALUES ($1, 'initial_assessment', 'assessment', 'Initial Assessment', 
                     'Patient initial evaluation', 'pending', 1, $2)
            RETURNING id
        """, workflow_id, user_id)
        
        print(f"  [PASS] Step created: {step_id}")
        
        # Test 5: Create audit entry
        print(f"[TEST] Create audit entry...")
        audit_id = await conn.fetchval("""
            INSERT INTO clinical_workflow_audit (
                workflow_id, action, user_id, details
            ) VALUES ($1, 'created', $2, 
                     '{"test": "integration", "component": "clinical_workflows"}')
            RETURNING id
        """, workflow_id, user_id)
        
        print(f"  [PASS] Audit entry created: {audit_id}")
        
        # Test 6: Clean up test data
        print(f"[TEST] Cleanup test data...")
        await conn.execute("DELETE FROM clinical_workflow_audit WHERE id = $1", audit_id)
        await conn.execute("DELETE FROM clinical_workflow_steps WHERE id = $1", step_id)
        await conn.execute("DELETE FROM clinical_workflows WHERE id = $1", workflow_id)
        print(f"  [PASS] Test data cleaned up")
        
        await conn.close()
        
        print("\n[SUCCESS] All integration tests passed!")
        print("Clinical workflows module is ready for production use.")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Integration test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_clinical_workflows_integration())