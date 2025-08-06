#!/usr/bin/env python3
"""
Clinical Workflows Migration for Docker Environment
Uses correct Docker PostgreSQL connection settings.
"""

import asyncpg
import asyncio
from datetime import datetime

async def create_clinical_workflows_tables():
    """Create clinical workflows tables with proper Docker connection."""
    
    try:
        # Connect using Docker PostgreSQL settings from docker-compose.yml
        conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
        
        print("Clinical Workflows Database Migration")
        print("=" * 50)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Connected to Docker PostgreSQL successfully!")
        
        # Step 1: Create clinical workflows table
        print("\nStep 1: Creating clinical_workflows table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS clinical_workflows (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                patient_id UUID NOT NULL,
                provider_id UUID NOT NULL,
                workflow_type VARCHAR(50) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'active',
                priority VARCHAR(50) NOT NULL DEFAULT 'routine',
                chief_complaint_encrypted TEXT,
                history_present_illness_encrypted TEXT,
                assessment_encrypted TEXT,
                plan_encrypted TEXT,
                location VARCHAR(255),
                department VARCHAR(255),
                estimated_duration_minutes INTEGER,
                actual_duration_minutes INTEGER,
                completion_percentage INTEGER DEFAULT 0,
                allergies_encrypted TEXT,
                current_medications_encrypted TEXT,
                started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP WITH TIME ZONE,
                last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_by UUID NOT NULL,
                updated_by UUID,
                version INTEGER DEFAULT 1,
                metadata JSONB DEFAULT '{}',
                
                -- Constraints
                CONSTRAINT check_completion_percentage 
                    CHECK (completion_percentage >= 0 AND completion_percentage <= 100),
                CONSTRAINT check_status 
                    CHECK (status IN ('active', 'completed', 'cancelled', 'paused', 'error')),
                CONSTRAINT check_priority 
                    CHECK (priority IN ('routine', 'urgent', 'emergency', 'critical')),
                CONSTRAINT check_workflow_type 
                    CHECK (workflow_type IN ('encounter', 'procedure', 'emergency', 'consultation', 'followup', 'admission', 'discharge', 'surgery'))
            );
        """)
        print("[SUCCESS] clinical_workflows table created")
        
        # Step 2: Create clinical workflow steps table
        print("\nStep 2: Creating clinical_workflow_steps table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS clinical_workflow_steps (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                workflow_id UUID NOT NULL REFERENCES clinical_workflows(id) ON DELETE CASCADE,
                step_name VARCHAR(255) NOT NULL,
                step_type VARCHAR(100) NOT NULL,
                step_order INTEGER NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                notes_encrypted TEXT,
                estimated_duration_minutes INTEGER,
                actual_duration_minutes INTEGER,
                started_at TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE,
                assigned_to UUID,
                completed_by UUID,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB DEFAULT '{}',
                
                -- Constraints
                CONSTRAINT check_step_status 
                    CHECK (status IN ('pending', 'in_progress', 'completed', 'skipped', 'failed')),
                CONSTRAINT check_step_type 
                    CHECK (step_type IN ('assessment', 'treatment', 'documentation', 'consultation', 'procedure', 'medication', 'discharge_planning', 'clinical_evaluation')),
                CONSTRAINT unique_workflow_step_order 
                    UNIQUE (workflow_id, step_order)
            );
        """)
        print("[SUCCESS] clinical_workflow_steps table created")
        
        # Step 3: Create clinical encounters table
        print("\nStep 3: Creating clinical_encounters table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS clinical_encounters (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                workflow_id UUID NOT NULL REFERENCES clinical_workflows(id) ON DELETE CASCADE,
                patient_id UUID NOT NULL,
                provider_id UUID NOT NULL,
                encounter_class VARCHAR(50) NOT NULL,
                encounter_type VARCHAR(100),
                service_type VARCHAR(100),
                diagnosis_codes TEXT[],
                procedure_codes TEXT[],
                billing_codes TEXT[],
                encounter_start TIMESTAMP WITH TIME ZONE NOT NULL,
                encounter_end TIMESTAMP WITH TIME ZONE,
                location VARCHAR(255),
                department VARCHAR(255),
                discharge_disposition VARCHAR(100),
                admission_source VARCHAR(100),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB DEFAULT '{}',
                
                -- Constraints
                CONSTRAINT check_encounter_class 
                    CHECK (encounter_class IN ('inpatient', 'outpatient', 'emergency', 'urgent_care', 'home_health', 'virtual'))
            );
        """)
        print("[SUCCESS] clinical_encounters table created")
        
        # Step 4: Create audit table
        print("\nStep 4: Creating clinical_workflow_audit table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS clinical_workflow_audit (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                workflow_id UUID NOT NULL,
                action VARCHAR(100) NOT NULL,
                user_id UUID NOT NULL,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                old_values JSONB,
                new_values JSONB,
                ip_address INET,
                user_agent TEXT,
                session_id VARCHAR(255),
                phi_accessed BOOLEAN DEFAULT FALSE,
                compliance_metadata JSONB DEFAULT '{}',
                
                -- Constraints
                CONSTRAINT check_audit_action 
                    CHECK (action IN ('created', 'updated', 'deleted', 'accessed', 'completed', 'cancelled', 'step_added', 'step_updated', 'step_completed', 'phi_accessed', 'status_changed'))
            );
        """)
        print("[SUCCESS] clinical_workflow_audit table created")
        
        # Step 5: Create indexes
        print("\nStep 5: Creating performance indexes...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflows_patient_id ON clinical_workflows(patient_id);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflows_provider_id ON clinical_workflows(provider_id);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflows_status ON clinical_workflows(status);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflows_priority ON clinical_workflows(priority);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflows_workflow_type ON clinical_workflows(workflow_type);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflow_steps_workflow_id ON clinical_workflow_steps(workflow_id);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflow_steps_status ON clinical_workflow_steps(status);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_encounters_workflow_id ON clinical_encounters(workflow_id);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_encounters_patient_id ON clinical_encounters(patient_id);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflow_audit_workflow_id ON clinical_workflow_audit(workflow_id);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflow_audit_timestamp ON clinical_workflow_audit(timestamp);"
        ]
        
        for index_sql in indexes:
            await conn.execute(index_sql)
        
        print(f"[SUCCESS] Created {len(indexes)} performance indexes")
        
        # Step 6: Verify tables
        print("\nStep 6: Verifying table creation...")
        
        tables_to_check = [
            'clinical_workflows',
            'clinical_workflow_steps', 
            'clinical_encounters',
            'clinical_workflow_audit'
        ]
        
        for table in tables_to_check:
            result = await conn.fetchval(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = '{table}'
                );
            """)
            print(f"[VERIFIED] Table {table}: {'EXISTS' if result else 'MISSING'}")
        
        await conn.close()
        
        print(f"\n[SUCCESS] CLINICAL WORKFLOWS MIGRATION COMPLETED!")
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nNext steps:")
        print("1. Start FastAPI server: python app/main.py")
        print("2. Test health endpoint: curl http://localhost:8000/api/v1/clinical-workflows/health")
        print("3. Run test suite with authentication")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        print("Please check:")
        print("1. Docker services are running: docker-compose up -d")
        print("2. PostgreSQL is accessible on localhost:5432")
        print("3. Database credentials are correct")
        return False

if __name__ == "__main__":
    print("Clinical Workflows Database Migration")
    print("Connecting to Docker PostgreSQL...")
    
    success = asyncio.run(create_clinical_workflows_tables())
    exit_code = 0 if success else 1
    exit(exit_code)