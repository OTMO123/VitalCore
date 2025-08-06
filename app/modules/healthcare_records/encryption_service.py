"""
Healthcare Records Encryption Service
Provides encryption functionality for PHI/PII data in healthcare records.
"""

from app.core.security import EncryptionService


async def get_encryption_service() -> EncryptionService:
    """
    Dependency injection function for EncryptionService.
    
    Returns:
        EncryptionService: Configured encryption service instance
    """
    return EncryptionService()