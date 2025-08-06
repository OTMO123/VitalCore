"""
Role Alias for Backward Compatibility
Provides Role alias for UserRole to fix import issues
"""

from app.core.database_unified import UserRole

# Backward compatibility alias
Role = UserRole

# Export for easy import
__all__ = ['Role', 'UserRole']
