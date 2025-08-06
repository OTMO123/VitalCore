"""
Marshmallow Compatibility Patch

Fixes the __version_info__ attribute error in marshmallow 4.0+
for backward compatibility with libraries expecting marshmallow 3.x API.
"""

import marshmallow
import sys
from packaging import version


def patch_marshmallow_compatibility():
    """
    Add __version_info__ attribute to marshmallow for backward compatibility.
    
    This fixes the AttributeError that occurs when libraries (like environs)
    try to access marshmallow.__version_info__ which was removed in v4.0.
    """
    if not hasattr(marshmallow, '__version_info__'):
        try:
            # Parse version string into tuple format
            v = version.parse(marshmallow.__version__)
            version_tuple = (v.major, v.minor, v.micro) if v.micro is not None else (v.major, v.minor, 0)
            
            # Add the missing attribute
            marshmallow.__version_info__ = version_tuple
            
            print(f"✅ Marshmallow compatibility patch applied: {marshmallow.__version__} -> {version_tuple}")
            
        except Exception as e:
            # Fallback to a reasonable default for marshmallow 4.x
            marshmallow.__version_info__ = (4, 0, 0)
            print(f"⚠️ Marshmallow compatibility patch fallback applied: {e}")
    
    return marshmallow.__version_info__


def check_marshmallow_compatibility():
    """Check if marshmallow compatibility patch is needed and working"""
    try:
        # Test access to __version_info__
        version_info = marshmallow.__version_info__
        print(f"✅ Marshmallow __version_info__ available: {version_info}")
        return True
    except AttributeError:
        print("❌ Marshmallow __version_info__ not available - patch needed")
        return False


# Apply patch immediately when module is imported
if __name__ != "__main__":
    # Only patch if we're being imported, not if script is run directly
    patch_marshmallow_compatibility()


if __name__ == "__main__":
    # Test script functionality
    print("Testing marshmallow compatibility patch...")
    
    print(f"Current marshmallow version: {marshmallow.__version__}")
    
    # Check before patch
    before_patch = check_marshmallow_compatibility()
    
    # Apply patch
    patch_result = patch_marshmallow_compatibility()
    
    # Check after patch
    after_patch = check_marshmallow_compatibility()
    
    print(f"Patch successful: {before_patch} -> {after_patch}")
    print(f"Final __version_info__: {marshmallow.__version_info__}")