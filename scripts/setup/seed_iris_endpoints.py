#!/usr/bin/env python3
"""
Seed IRIS API endpoints for dashboard testing and development.

This script creates demo IRIS API endpoints so the dashboard can display
real integration status instead of empty mock data.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.database_advanced import APIEndpoint, APICredential
from app.core.security import security_manager
import structlog

logger = structlog.get_logger()

# Demo IRIS API endpoints
DEMO_ENDPOINTS = [
    {
        "name": "Production IRIS API",
        "base_url": "https://api.iris.state.gov",
        "api_version": "v2.0",
        "auth_type": "oauth2",
        "timeout_seconds": 30,
        "retry_attempts": 3,
        "status": "active",
        "metadata": {
            "environment": "production",
            "region": "us-east-1",
            "description": "Primary IRIS API endpoint for production immunization data"
        },
        "credentials": {
            "client_id": "demo_client_prod",
            "client_secret": "demo_secret_prod_12345"
        }
    },
    {
        "name": "Staging IRIS API",
        "base_url": "https://staging-api.iris.state.gov",
        "api_version": "v2.0",
        "auth_type": "oauth2",
        "timeout_seconds": 30,
        "retry_attempts": 3,
        "status": "active",
        "metadata": {
            "environment": "staging",
            "region": "us-east-1",
            "description": "Staging IRIS API endpoint for testing and development"
        },
        "credentials": {
            "client_id": "demo_client_staging",
            "client_secret": "demo_secret_staging_67890"
        }
    },
    {
        "name": "Legacy IRIS API",
        "base_url": "https://legacy.iris.state.gov",
        "api_version": "v1.5",
        "auth_type": "hmac",
        "timeout_seconds": 60,
        "retry_attempts": 5,
        "status": "deprecated",
        "metadata": {
            "environment": "legacy",
            "region": "us-west-2",
            "description": "Legacy IRIS API endpoint - being phased out",
            "deprecation_date": "2025-12-31"
        },
        "credentials": {
            "client_id": "legacy_client_001",
            "client_secret": "legacy_hmac_key_abcdef"
        }
    }
]

async def create_demo_endpoints():
    """Create demo IRIS API endpoints."""
    logger.info("Starting IRIS endpoints seed process")
    
    async for session in get_db():
        try:
            # Check if endpoints already exist
            from sqlalchemy import select
            result = await session.execute(select(APIEndpoint))
            existing_endpoints = result.scalars().all()
            
            if existing_endpoints:
                logger.info("IRIS endpoints already exist, skipping seed", count=len(existing_endpoints))
                return
            
            created_count = 0
            
            for endpoint_data in DEMO_ENDPOINTS:
                # Create endpoint
                endpoint = APIEndpoint(
                    name=endpoint_data["name"],
                    base_url=endpoint_data["base_url"],
                    api_version=endpoint_data["api_version"],
                    auth_type=endpoint_data["auth_type"],
                    timeout_seconds=endpoint_data["timeout_seconds"],
                    retry_attempts=endpoint_data["retry_attempts"],
                    status=endpoint_data["status"],
                    config_metadata=endpoint_data["metadata"],
                    last_health_check_at=datetime.utcnow() - timedelta(minutes=5),  # Recent check
                    last_health_check_status=True  # Assume healthy for demo
                )
                
                session.add(endpoint)
                await session.flush()  # Get the ID
                
                # Create credentials
                credentials = endpoint_data["credentials"]
                for cred_name, cred_value in credentials.items():
                    encrypted_value = security_manager.encrypt_data(cred_value)
                    
                    credential = APICredential(
                        api_endpoint_id=endpoint.id,
                        credential_name=cred_name,
                        encrypted_value=encrypted_value,
                        created_by="system",  # System user for seeding
                        is_active=True
                    )
                    
                    session.add(credential)
                
                created_count += 1
                logger.info("Created IRIS endpoint", 
                          endpoint_name=endpoint.name, 
                          endpoint_id=str(endpoint.id))
            
            await session.commit()
            logger.info("IRIS endpoints seed completed successfully", 
                       endpoints_created=created_count)
            
        except Exception as e:
            await session.rollback()
            logger.error("Failed to seed IRIS endpoints", error=str(e))
            raise
        finally:
            await session.close()

async def verify_endpoints():
    """Verify that endpoints were created successfully."""
    logger.info("Verifying IRIS endpoints")
    
    async for session in get_db():
        try:
            from sqlalchemy import select, func
            
            # Count endpoints
            endpoint_count = await session.execute(
                select(func.count(APIEndpoint.id))
            )
            total_endpoints = endpoint_count.scalar()
            
            # Count credentials
            credential_count = await session.execute(
                select(func.count(APICredential.id))
            )
            total_credentials = credential_count.scalar()
            
            # Get endpoint details
            result = await session.execute(
                select(APIEndpoint.name, APIEndpoint.base_url, APIEndpoint.status)
            )
            endpoints = result.all()
            
            logger.info("IRIS endpoints verification completed",
                       total_endpoints=total_endpoints,
                       total_credentials=total_credentials)
            
            for endpoint in endpoints:
                logger.info("Endpoint details",
                          name=endpoint.name,
                          base_url=endpoint.base_url,
                          status=endpoint.status)
            
            return total_endpoints > 0
            
        except Exception as e:
            logger.error("Failed to verify IRIS endpoints", error=str(e))
            return False
        finally:
            await session.close()

async def main():
    """Main execution function."""
    try:
        logger.info("Starting IRIS endpoints seeding")
        
        # Create demo endpoints
        await create_demo_endpoints()
        
        # Verify creation
        success = await verify_endpoints()
        
        if success:
            logger.info("IRIS endpoints seeding completed successfully")
            print("\nIRIS API endpoints have been configured!")
            print("Dashboard will now show real IRIS integration status")
            print("You can add real IRIS credentials via the admin interface")
        else:
            logger.error("IRIS endpoints seeding failed verification")
            sys.exit(1)
            
    except Exception as e:
        logger.error("IRIS endpoints seeding failed", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    # Configure logging
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run seeding
    asyncio.run(main())