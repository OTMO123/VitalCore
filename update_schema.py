#!/usr/bin/env python3
"""
Update Clinical Workflows Schema
Add missing columns to match the model definitions.
"""
import asyncpg
import asyncio

async def update_schema():
    try:
        conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
        print("Updating clinical workflows schema...")
        
        # Add missing columns to clinical_workflows
        print("Adding missing columns to clinical_workflows...")
        
        columns_to_add = [
            ("organization_id", "UUID REFERENCES organizations(id) ON DELETE SET NULL"),
            ("title", "VARCHAR(255) NOT NULL DEFAULT 'Clinical Workflow'"),
            ("description", "TEXT"),
            ("severity", "VARCHAR(50) DEFAULT 'moderate'"),
            ("risk_level", "INTEGER DEFAULT 50"),
            ("emergency", "BOOLEAN DEFAULT FALSE"),
            ("consent_obtained", "BOOLEAN DEFAULT FALSE"),
            ("consent_details", "TEXT"),
            ("structured_data_encrypted", "TEXT"),
            ("deleted_at", "TIMESTAMPTZ"),
            ("deleted_by", "UUID")
        ]
        
        for col_name, col_def in columns_to_add:
            try:
                await conn.execute(f"ALTER TABLE clinical_workflows ADD COLUMN IF NOT EXISTS {col_name} {col_def};")
                print(f"  [SUCCESS] Added {col_name}")
            except Exception as e:
                print(f"  [INFO] {col_name} - {e}")
        
        # Add missing columns to clinical_workflow_steps
        print("Adding missing columns to clinical_workflow_steps...")
        
        step_columns = [
            ("title", "VARCHAR(255) NOT NULL DEFAULT 'Workflow Step'"),
            ("description", "TEXT"),
            ("step_type", "VARCHAR(100) NOT NULL DEFAULT 'task'"),
            ("step_order", "INTEGER NOT NULL DEFAULT 1"),
            ("estimated_duration_minutes", "INTEGER"),
            ("actual_duration_minutes", "INTEGER"),
            ("assigned_to", "UUID REFERENCES users(id) ON DELETE SET NULL"),
            ("due_date", "TIMESTAMPTZ"),
            ("started_at", "TIMESTAMPTZ"),
            ("completed_at", "TIMESTAMPTZ"),
            ("step_data_encrypted", "TEXT"),
            ("validation_rules", "JSONB"),
            ("created_by", "UUID NOT NULL"),
            ("updated_by", "UUID"),
            ("deleted_at", "TIMESTAMPTZ"),
            ("deleted_by", "UUID")
        ]
        
        for col_name, col_def in step_columns:
            try:
                await conn.execute(f"ALTER TABLE clinical_workflow_steps ADD COLUMN IF NOT EXISTS {col_name} {col_def};")
                print(f"  [SUCCESS] Added {col_name}")
            except Exception as e:
                print(f"  [INFO] {col_name} - {e}")
        
        # Add missing columns to clinical_encounters  
        print("Adding missing columns to clinical_encounters...")
        
        encounter_columns = [
            ("workflow_id", "UUID REFERENCES clinical_workflows(id) ON DELETE CASCADE"),
            ("encounter_class", "VARCHAR(50) NOT NULL DEFAULT 'outpatient'"),
            ("encounter_type", "VARCHAR(100)"),
            ("location", "VARCHAR(255)"),
            ("service_provider", "UUID REFERENCES providers(id) ON DELETE SET NULL"),
            ("started_at", "TIMESTAMPTZ NOT NULL DEFAULT NOW()"),
            ("ended_at", "TIMESTAMPTZ"),
            ("length_minutes", "INTEGER"),
            ("discharge_disposition", "VARCHAR(100)"),
            ("fhir_encounter_data", "JSONB"),
            ("created_by", "UUID NOT NULL"),
            ("updated_by", "UUID")
        ]
        
        for col_name, col_def in encounter_columns:
            try:
                await conn.execute(f"ALTER TABLE clinical_encounters ADD COLUMN IF NOT EXISTS {col_name} {col_def};")
                print(f"  [SUCCESS] Added {col_name}")
            except Exception as e:
                print(f"  [INFO] {col_name} - {e}")
        
        # Update audit table if needed
        print("Updating clinical_workflow_audit...")
        audit_columns = [
            ("action", "VARCHAR(100) NOT NULL DEFAULT 'unknown'"),
            ("user_id", "UUID NOT NULL"),
            ("details", "JSONB DEFAULT '{}'"),
            ("ip_address", "INET"),
            ("user_agent", "TEXT"),
            ("timestamp", "TIMESTAMPTZ NOT NULL DEFAULT NOW()")
        ]
        
        for col_name, col_def in audit_columns:
            try:
                await conn.execute(f"ALTER TABLE clinical_workflow_audit ADD COLUMN IF NOT EXISTS {col_name} {col_def};")
                print(f"  [SUCCESS] Added {col_name}")
            except Exception as e:
                print(f"  [INFO] {col_name} - {e}")
        
        print("\n[SUCCESS] Schema update completed!")
        await conn.close()
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(update_schema())