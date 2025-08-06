#!/usr/bin/env python3
"""
Clinical Workflows Database Migration
Creates all required tables and indexes for clinical workflows module.
"""

import asyncpg
import asyncio
from datetime import datetime

async def create_clinical_workflows_tables():
    """Create clinical workflows tables with proper indexes and constraints."""
    
    try:
        # Connect to the database
        conn = await asyncpg.connect("postgresql://test_user:test_password@localhost:5433/test_iris_db")
        
        print("🏥 CLINICAL WORKFLOWS MIGRATION")
        print("=" * 50)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Create clinical workflows table
        print("\n📋 Step 1: Creating clinical_workflows table...")
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
        print("✓ clinical_workflows table created")
        
        # Step 2: Create clinical workflow steps table
        print("\n📋 Step 2: Creating clinical_workflow_steps table...")
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
        print("✓ clinical_workflow_steps table created")
        
        # Step 3: Create clinical encounters table
        print("\n📋 Step 3: Creating clinical_encounters table...")
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
        print("✓ clinical_encounters table created")
        
        # Step 4: Create audit table for clinical workflows
        print("\n📋 Step 4: Creating clinical_workflow_audit table...")
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
        print("✓ clinical_workflow_audit table created")
        
        # Step 5: Create performance indexes
        print("\n📋 Step 5: Creating performance indexes...")
        
        indexes = [
            # Clinical workflows indexes
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflows_patient_id ON clinical_workflows(patient_id);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflows_provider_id ON clinical_workflows(provider_id);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflows_status ON clinical_workflows(status);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflows_priority ON clinical_workflows(priority);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflows_workflow_type ON clinical_workflows(workflow_type);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflows_started_at ON clinical_workflows(started_at);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflows_department ON clinical_workflows(department);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflows_completion ON clinical_workflows(completion_percentage);",
            
            # Clinical workflow steps indexes
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflow_steps_workflow_id ON clinical_workflow_steps(workflow_id);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflow_steps_status ON clinical_workflow_steps(status);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflow_steps_assigned_to ON clinical_workflow_steps(assigned_to);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflow_steps_order ON clinical_workflow_steps(workflow_id, step_order);",
            
            # Clinical encounters indexes
            "CREATE INDEX IF NOT EXISTS idx_clinical_encounters_workflow_id ON clinical_encounters(workflow_id);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_encounters_patient_id ON clinical_encounters(patient_id);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_encounters_provider_id ON clinical_encounters(provider_id);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_encounters_class ON clinical_encounters(encounter_class);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_encounters_start ON clinical_encounters(encounter_start);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_encounters_department ON clinical_encounters(department);",
            
            # Audit indexes
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflow_audit_workflow_id ON clinical_workflow_audit(workflow_id);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflow_audit_user_id ON clinical_workflow_audit(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflow_audit_timestamp ON clinical_workflow_audit(timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflow_audit_action ON clinical_workflow_audit(action);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflow_audit_phi ON clinical_workflow_audit(phi_accessed);",
            
            # Composite indexes for common queries
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflows_patient_status ON clinical_workflows(patient_id, status);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflows_provider_status ON clinical_workflows(provider_id, status);",
            "CREATE INDEX IF NOT EXISTS idx_clinical_workflows_department_priority ON clinical_workflows(department, priority);",
        ]
        
        for index_sql in indexes:
            await conn.execute(index_sql)
            print(f"✓ Index created: {index_sql.split('idx_')[1].split(' ')[0] if 'idx_' in index_sql else 'index'}")
        
        # Step 6: Verify tables and get counts
        print("\n📋 Step 6: Verifying table creation...")
        
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
            print(f"✓ Table {table}: {'EXISTS' if result else 'MISSING'}")
        
        # Step 7: Show table relationships
        print("\n📋 Step 7: Table relationship summary...")
        print("""
        Table Relationships:
        ==================
        clinical_workflows (main table)
        ├── clinical_workflow_steps (1:N) - Steps within a workflow
        ├── clinical_encounters (1:N) - Associated encounters  
        └── clinical_workflow_audit (1:N) - Audit trail
        
        Key Features:
        - PHI/PII fields are encrypted (_encrypted suffix)
        - Full audit trail for compliance (HIPAA/SOC2)
        - Performance indexes for fast queries
        - FHIR R4 compatible structure
        - Role-based access control ready
        """)
        
        await conn.close()
        
        print(f"\n🎉 CLINICAL WORKFLOWS MIGRATION SUCCESSFUL!")
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nNext steps:")
        print("1. Integrate router into main FastAPI app")
        print("2. Run comprehensive test suite")
        print("3. Verify health check endpoints")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("Check database connection and retry.")
        raise

if __name__ == "__main__":
    asyncio.run(create_clinical_workflows_tables())