#!/usr/bin/env python3
"""
Migrate database schema to match current models
"""

import asyncio
import asyncpg
import uuid

async def migrate_schema():
    # Connect to database
    conn = await asyncpg.connect("postgresql://postgres:password@localhost:5432/iris_db")
    
    try:
        print("Starting schema migration...")
        
        # Start transaction
        async with conn.transaction():
            
            # Check if we need to migrate users table
            columns = await conn.fetch("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'users'
            """)
            column_names = [col['column_name'] for col in columns]
            
            if 'hashed_password' in column_names and 'password_hash' not in column_names:
                print("Migrating users table...")
                
                # Add new UUID id column
                await conn.execute("ALTER TABLE users ADD COLUMN new_id UUID DEFAULT gen_random_uuid()")
                
                # Add missing columns
                await conn.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)")
                await conn.execute("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT TRUE")
                await conn.execute("ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN DEFAULT FALSE")
                await conn.execute("ALTER TABLE users ADD COLUMN must_change_password BOOLEAN DEFAULT FALSE")
                await conn.execute("ALTER TABLE users ADD COLUMN password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                await conn.execute("ALTER TABLE users ADD COLUMN is_system_user BOOLEAN DEFAULT FALSE")
                await conn.execute("ALTER TABLE users ADD COLUMN profile_data JSON")
                
                # Copy data from old columns to new ones
                await conn.execute("UPDATE users SET password_hash = hashed_password")
                await conn.execute("UPDATE users SET email_verified = is_verified")
                
                # For simplicity, let's just recreate the table with the correct schema
                # First backup existing users
                users = await conn.fetch("SELECT * FROM users")
                
                # Drop the old table
                await conn.execute("DROP TABLE IF EXISTS users CASCADE")
                
                # Create the new table with correct schema
                await conn.execute("""
                    CREATE TABLE users (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        username VARCHAR(50) UNIQUE NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        role VARCHAR(20) NOT NULL DEFAULT 'user',
                        is_active BOOLEAN NOT NULL DEFAULT TRUE,
                        email_verified BOOLEAN NOT NULL DEFAULT FALSE,
                        mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
                        failed_login_attempts INTEGER NOT NULL DEFAULT 0,
                        last_login TIMESTAMP,
                        locked_until TIMESTAMP,
                        must_change_password BOOLEAN NOT NULL DEFAULT FALSE,
                        password_changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        is_system_user BOOLEAN NOT NULL DEFAULT FALSE,
                        profile_data JSON,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
                        deleted_at TIMESTAMP
                    )
                """)
                
                # Restore users with new schema
                for user in users:
                    await conn.execute("""
                        INSERT INTO users (
                            username, email, password_hash, role, is_active, 
                            email_verified, failed_login_attempts, last_login, 
                            locked_until, created_at, updated_at, is_deleted, deleted_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    """, 
                    user['username'], user['email'], user['hashed_password'], 
                    user['role'], user['is_active'], user['is_verified'],
                    user['failed_login_attempts'], user['last_login'], 
                    user['locked_until'], user['created_at'], user['updated_at'],
                    user['is_deleted'], user['deleted_at'])
                
                print("Users table migrated successfully!")
            else:
                print("Users table already has correct schema")
        
        print("Schema migration completed!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate_schema())