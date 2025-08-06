#!/usr/bin/env python3
"""
Add Missing Referenced Tables for Clinical Workflows
Creates organizations and providers tables that are referenced by clinical workflows.
"""
import asyncpg
import asyncio
from datetime import datetime

async def add_missing_tables():
    """Add missing organizations and providers tables."""
    try:
        conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
        print("Connected to PostgreSQL successfully!")
        
        print("\nAdding missing tables for clinical workflows...")
        
        # Create organizations table
        print("Creating organizations table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS organizations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                type VARCHAR(100) NOT NULL DEFAULT 'healthcare_provider',
                npi VARCHAR(10) UNIQUE,
                tax_id VARCHAR(20),
                address_line1 VARCHAR(255),
                address_line2 VARCHAR(255),
                city VARCHAR(100),
                state VARCHAR(50),
                zip_code VARCHAR(20),
                country VARCHAR(100) DEFAULT 'US',
                phone VARCHAR(50),
                email VARCHAR(255),
                website VARCHAR(255),
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                created_by UUID,
                updated_by UUID
            );
        """)
        print("  [SUCCESS] organizations table created")
        
        # Create providers table
        print("Creating providers table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS providers (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
                provider_type VARCHAR(100) NOT NULL DEFAULT 'physician',
                npi VARCHAR(10) UNIQUE,
                license_number VARCHAR(100),
                license_state VARCHAR(50),
                license_expiry DATE,
                specialty VARCHAR(255),
                board_certifications TEXT[],
                dea_number VARCHAR(20),
                credentials VARCHAR(255),
                department VARCHAR(255),
                title VARCHAR(255),
                phone VARCHAR(50),
                email VARCHAR(255),
                status VARCHAR(50) DEFAULT 'active',
                hire_date DATE,
                termination_date DATE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                created_by UUID,
                updated_by UUID
            );
        """)
        print("  [SUCCESS] providers table created")
        
        # Add indexes for performance
        print("Creating indexes...")
        
        # Organizations indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_organizations_npi ON organizations(npi);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_organizations_status ON organizations(status);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_organizations_type ON organizations(type);")
        
        # Providers indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_providers_user_id ON providers(user_id);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_providers_organization_id ON providers(organization_id);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_providers_npi ON providers(npi);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_providers_status ON providers(status);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_providers_specialty ON providers(specialty);")
        
        print("  [SUCCESS] Indexes created")
        
        # Insert sample data
        print("Inserting sample data...")
        
        # Sample organization
        org_result = await conn.fetchrow("""
            INSERT INTO organizations (name, type, npi, address_line1, city, state, zip_code, phone)
            VALUES ('General Hospital', 'hospital', '1234567890', '123 Medical Center Dr', 'Healthcare City', 'CA', '90210', '555-0100')
            ON CONFLICT (npi) DO NOTHING
            RETURNING id;
        """)
        
        if org_result:
            org_id = org_result['id']
            print(f"  [SUCCESS] Sample organization created: {org_id}")
        else:
            # Get existing organization
            org_result = await conn.fetchrow("SELECT id FROM organizations WHERE npi = '1234567890';")
            org_id = org_result['id'] if org_result else None
            print("  [INFO] Sample organization already exists")
        
        # Sample provider (if we have a user to reference)
        user_result = await conn.fetchrow("SELECT id FROM users LIMIT 1;")
        if user_result and org_id:
            await conn.execute("""
                INSERT INTO providers (user_id, organization_id, provider_type, npi, specialty, credentials)
                VALUES ($1, $2, 'physician', '9876543210', 'Internal Medicine', 'MD')
                ON CONFLICT (npi) DO NOTHING;
            """, user_result['id'], org_id)
            print("  [SUCCESS] Sample provider created")
        
        # Verify tables exist
        print("\nVerifying tables...")
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('organizations', 'providers');
        """)
        
        for table in tables:
            print(f"  [VERIFIED] {table['table_name']}")
        
        await conn.close()
        
        print(f"\n[SUCCESS] Missing tables migration completed!")
        print("Clinical workflows should now work without foreign key errors.")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(add_missing_tables())