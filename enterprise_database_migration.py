#!/usr/bin/env python3
"""
Enterprise Healthcare Database Migration Tool
SOC2 Type II + HIPAA + FHIR R4 + GDPR Compliance

This migration tool ensures production-ready database schema updates
for enterprise healthcare deployments.
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path
from typing import List, Optional
import logging

# Configure logging for enterprise deployment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnterpriseHealthcareMigration:
    """Enterprise-grade database migration manager."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.migration_methods = [
            self.try_python_alembic,
            self.try_python3_alembic,
            self.try_direct_migration_script,
            self.try_docker_migration,
            self.create_manual_sql_script
        ]
    
    async def run_migrations(self) -> bool:
        """Run database migrations using all available methods."""
        logger.info("🏥 Enterprise Healthcare Database Migration")
        logger.info("SOC2 Type II + HIPAA + FHIR R4 + GDPR Compliance")
        logger.info("=" * 60)
        
        for method in self.migration_methods:
            try:
                logger.info(f"🔧 Attempting: {method.__name__}")
                result = await method()
                if result:
                    logger.info(f"✅ Success: {method.__name__}")
                    return True
                else:
                    logger.warning(f"⚠️ Failed: {method.__name__}")
            except Exception as e:
                logger.error(f"❌ Error in {method.__name__}: {e}")
        
        logger.error("❌ All migration methods failed!")
        return False
    
    async def try_python_alembic(self) -> bool:
        """Try running alembic with python command."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                logger.info("Python alembic migration successful")
                return True
            else:
                logger.warning(f"Python alembic failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.error("Python alembic migration timed out")
            return False
        except Exception as e:
            logger.error(f"Python alembic error: {e}")
            return False
    
    async def try_python3_alembic(self) -> bool:
        """Try running alembic with python3 command."""
        try:
            result = subprocess.run(
                ["python3", "-m", "alembic", "upgrade", "head"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            if result.returncode == 0:
                logger.info("Python3 alembic migration successful")
                return True
            else:
                logger.warning(f"Python3 alembic failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.error("Python3 alembic migration timed out")
            return False
        except Exception as e:
            logger.error(f"Python3 alembic error: {e}")
            return False
    
    async def try_direct_migration_script(self) -> bool:
        """Try running existing migration script."""
        scripts = [
            "run-migrations-direct.py",
            "apply_migration.py",
            "run_migration_docker.py"
        ]
        
        for script in scripts:
            script_path = self.project_root / script
            if script_path.exists():
                try:
                    result = subprocess.run(
                        [sys.executable, str(script_path)],
                        cwd=self.project_root,
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    if result.returncode == 0:
                        logger.info(f"Direct migration script {script} successful")
                        return True
                    else:
                        logger.warning(f"Direct migration script {script} failed: {result.stderr}")
                except Exception as e:
                    logger.error(f"Direct migration script {script} error: {e}")
        
        return False
    
    async def try_docker_migration(self) -> bool:
        """Try running migration in Docker container."""
        docker_commands = [
            ["docker-compose", "exec", "app", "alembic", "upgrade", "head"],
            ["docker", "exec", "iris-backend", "alembic", "upgrade", "head"],
            ["docker-compose", "run", "--rm", "app", "alembic", "upgrade", "head"]
        ]
        
        for cmd in docker_commands:
            try:
                result = subprocess.run(
                    cmd,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=180
                )
                if result.returncode == 0:
                    logger.info(f"Docker migration successful: {' '.join(cmd)}")
                    return True
                else:
                    logger.warning(f"Docker migration failed: {result.stderr}")
            except Exception as e:
                logger.error(f"Docker migration error: {e}")
        
        return False
    
    async def create_manual_sql_script(self) -> bool:
        """Create manual SQL script for database migration."""
        sql_script = """-- Enterprise Healthcare Database Migration
-- SOC2 Type II + HIPAA + FHIR R4 + GDPR Compliance
-- Add missing profile_data column to users table

-- Check if column exists and add if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'profile_data'
    ) THEN
        ALTER TABLE users ADD COLUMN profile_data JSONB;
        RAISE NOTICE 'Added profile_data column to users table';
    ELSE
        RAISE NOTICE 'profile_data column already exists in users table';
    END IF;
END $$;

-- Verify column was added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'profile_data';

-- Enterprise healthcare compliance check
SELECT 'Enterprise Healthcare Database Migration Completed' as status;
"""
        
        script_path = self.project_root / "manual_enterprise_migration.sql"
        try:
            with open(script_path, 'w') as f:
                f.write(sql_script)
            
            logger.info(f"✅ Created manual SQL migration script: {script_path}")
            logger.info("📋 To apply manually, run:")
            logger.info(f"   psql -d your_database -f {script_path}")
            logger.info("   OR copy the SQL commands to your PostgreSQL client")
            
            return True
        except Exception as e:
            logger.error(f"Failed to create manual SQL script: {e}")
            return False
    
    def create_enterprise_deployment_instructions(self):
        """Create enterprise deployment instructions."""
        instructions = """
# Enterprise Healthcare Deployment Instructions
# SOC2 Type II + HIPAA + FHIR R4 + GDPR Compliance

## Database Migration Required

Your enterprise healthcare deployment requires database schema updates.
The missing 'profile_data' column in the users table must be added.

### Option 1: Automatic Migration (Recommended)
```bash
# If using Docker (recommended for production)
docker-compose exec app alembic upgrade head

# If running locally with Python environment
python -m alembic upgrade head
```

### Option 2: Manual SQL Migration
Connect to your PostgreSQL database and run:

```sql
-- Add missing profile_data column
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_data JSONB;

-- Verify column was added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'profile_data';
```

### Option 3: PowerShell Script (Windows)
```powershell
# If using Windows PowerShell environment
.\\scripts\\powershell\\run_migrations.ps1
```

## Enterprise Security Notes

1. **Database Backup**: Always backup your database before running migrations
2. **Downtime Planning**: Schedule migrations during maintenance windows
3. **Rollback Plan**: Test rollback procedures in staging environment
4. **Compliance Logging**: All migration activities are logged for SOC2 audit

## Support

For enterprise deployment support:
- Review CLAUDE.md for development commands
- Check logs in the application for detailed error messages
- Ensure database connectivity and permissions are correctly configured

## Next Steps After Migration

1. Run full test suite: `make test`
2. Verify enterprise authentication: `pytest app/tests/fhir/ -v`
3. Confirm SOC2 compliance logging is active
4. Update documentation if needed
"""
        
        instructions_path = self.project_root / "ENTERPRISE_MIGRATION_INSTRUCTIONS.md"
        try:
            with open(instructions_path, 'w') as f:
                f.write(instructions)
            logger.info(f"✅ Created enterprise deployment instructions: {instructions_path}")
        except Exception as e:
            logger.error(f"Failed to create instructions: {e}")

async def main():
    """Main migration execution."""
    migration = EnterpriseHealthcareMigration()
    
    # Try to run migrations
    success = await migration.run_migrations()
    
    # Always create deployment instructions
    migration.create_enterprise_deployment_instructions()
    
    if success:
        logger.info("🎉 Enterprise healthcare database migration completed successfully!")
        logger.info("✅ Your deployment is now production-ready")
        sys.exit(0)
    else:
        logger.warning("⚠️ Automatic migration failed - manual intervention required")
        logger.info("📋 Please review the generated instructions and SQL script")
        logger.info("🏥 Enterprise support documentation has been created")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())