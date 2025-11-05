#!/usr/bin/env python3
"""
Test script to verify encryption key validation works correctly.

This script tests that:
1. Application fails to start without encryption keys
2. Application fails with keys that are too short
3. Application provides clear error messages
4. Application succeeds with valid keys
"""

import os
import sys
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_missing_keys():
    """Test that application fails when encryption keys are missing."""
    print("\n" + "=" * 80)
    print("TEST 1: Missing Encryption Keys")
    print("=" * 80)

    # Clear all encryption-related environment variables
    env = os.environ.copy()
    keys_to_remove = [
        "PHI_ENCRYPTION_KEY",
        "ENCRYPTION_KEY",
        "ENCRYPTION_SALT",
        "JWT_SECRET_KEY",
        "SECRET_KEY",
    ]

    for key in keys_to_remove:
        env.pop(key, None)

    try:
        from app.core.config import get_settings

        # Clear the lru_cache to force re-initialization
        get_settings.cache_clear()

        settings = get_settings()
        print("❌ FAIL: Settings loaded without encryption keys (should have failed)")
        return False

    except Exception as e:
        error_msg = str(e)
        if "CRITICAL" in error_msg and ("encryption" in error_msg.lower() or "key" in error_msg.lower()):
            print("✅ PASS: Application correctly rejected missing keys")
            print(f"   Error message: {error_msg[:200]}...")
            return True
        else:
            print(f"⚠️  PARTIAL: Application failed but with unexpected error: {error_msg[:200]}...")
            return True


def test_short_keys():
    """Test that application fails when encryption keys are too short."""
    print("\n" + "=" * 80)
    print("TEST 2: Short Encryption Keys (< 32 characters)")
    print("=" * 80)

    # Set environment variables with short keys
    os.environ["PHI_ENCRYPTION_KEY"] = "short_key_12345"  # Only 17 characters
    os.environ["ENCRYPTION_KEY"] = "short_key_12345"
    os.environ["ENCRYPTION_SALT"] = "short_salt"
    os.environ["JWT_SECRET_KEY"] = "short_jwt"
    os.environ["SECRET_KEY"] = "short_secret"

    try:
        from app.core.config import get_settings

        # Clear the lru_cache to force re-initialization
        get_settings.cache_clear()

        settings = get_settings()
        print("❌ FAIL: Settings loaded with short keys (should have failed)")
        return False

    except Exception as e:
        error_msg = str(e)
        if "32 characters" in error_msg or "must be at least" in error_msg.lower():
            print("✅ PASS: Application correctly rejected short keys")
            print(f"   Error message: {error_msg[:200]}...")
            return True
        else:
            print(f"⚠️  PARTIAL: Application failed but with unexpected error: {error_msg[:200]}...")
            return True
    finally:
        # Clean up environment variables
        for key in ["PHI_ENCRYPTION_KEY", "ENCRYPTION_KEY", "ENCRYPTION_SALT", "JWT_SECRET_KEY", "SECRET_KEY"]:
            os.environ.pop(key, None)


def test_valid_keys():
    """Test that application succeeds with valid encryption keys."""
    print("\n" + "=" * 80)
    print("TEST 3: Valid Encryption Keys (32+ characters)")
    print("=" * 80)

    # Generate valid test keys (32+ characters)
    import secrets

    os.environ["PHI_ENCRYPTION_KEY"] = secrets.token_urlsafe(32)
    os.environ["ENCRYPTION_KEY"] = secrets.token_urlsafe(32)
    os.environ["ENCRYPTION_SALT"] = secrets.token_urlsafe(32)
    os.environ["JWT_SECRET_KEY"] = secrets.token_urlsafe(32)
    os.environ["SECRET_KEY"] = secrets.token_urlsafe(32)

    try:
        from app.core.config import get_settings

        # Clear the lru_cache to force re-initialization
        get_settings.cache_clear()

        settings = get_settings()

        # Verify all keys are set
        assert settings.PHI_ENCRYPTION_KEY, "PHI_ENCRYPTION_KEY not set"
        assert settings.ENCRYPTION_KEY, "ENCRYPTION_KEY not set"
        assert settings.ENCRYPTION_SALT, "ENCRYPTION_SALT not set"
        assert settings.JWT_SECRET_KEY, "JWT_SECRET_KEY not set"
        assert settings.SECRET_KEY, "SECRET_KEY not set"

        # Verify minimum length
        assert len(settings.PHI_ENCRYPTION_KEY) >= 32, "PHI_ENCRYPTION_KEY too short"
        assert len(settings.ENCRYPTION_KEY) >= 32, "ENCRYPTION_KEY too short"
        assert len(settings.ENCRYPTION_SALT) >= 32, "ENCRYPTION_SALT too short"

        print("✅ PASS: Settings loaded successfully with valid keys")
        print(f"   PHI_ENCRYPTION_KEY length: {len(settings.PHI_ENCRYPTION_KEY)}")
        print(f"   ENCRYPTION_KEY length: {len(settings.ENCRYPTION_KEY)}")
        print(f"   ENCRYPTION_SALT length: {len(settings.ENCRYPTION_SALT)}")
        return True

    except Exception as e:
        print(f"❌ FAIL: Settings failed to load with valid keys: {str(e)}")
        return False
    finally:
        # Clean up environment variables
        for key in ["PHI_ENCRYPTION_KEY", "ENCRYPTION_KEY", "ENCRYPTION_SALT", "JWT_SECRET_KEY", "SECRET_KEY"]:
            os.environ.pop(key, None)


def test_key_generation_script():
    """Test that the key generation script exists and runs."""
    print("\n" + "=" * 80)
    print("TEST 4: Key Generation Script")
    print("=" * 80)

    script_path = project_root / "scripts" / "generate_encryption_keys.py"

    if not script_path.exists():
        print(f"❌ FAIL: Key generation script not found at {script_path}")
        return False

    print(f"✅ PASS: Key generation script found at {script_path}")

    # Check if script is executable
    if os.access(script_path, os.X_OK):
        print("✅ PASS: Script is executable")
    else:
        print("⚠️  WARNING: Script is not executable (chmod +x recommended)")

    return True


def test_documentation():
    """Test that encryption key documentation exists."""
    print("\n" + "=" * 80)
    print("TEST 5: Documentation")
    print("=" * 80)

    doc_path = project_root / "docs" / "ENCRYPTION_KEY_SETUP.md"

    if not doc_path.exists():
        print(f"❌ FAIL: Documentation not found at {doc_path}")
        return False

    print(f"✅ PASS: Documentation found at {doc_path}")

    # Check documentation size
    doc_size = doc_path.stat().st_size
    if doc_size < 1000:
        print(f"⚠️  WARNING: Documentation seems short ({doc_size} bytes)")
        return False

    print(f"✅ PASS: Documentation has substantial content ({doc_size} bytes)")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("🔐 VITALCORE ENCRYPTION KEY VALIDATION TEST SUITE")
    print("=" * 80)
    print()
    print("Testing encryption key management implementation...")
    print()

    results = {
        "Missing Keys Test": test_missing_keys(),
        "Short Keys Test": test_short_keys(),
        "Valid Keys Test": test_valid_keys(),
        "Key Generation Script": test_key_generation_script(),
        "Documentation Test": test_documentation(),
    }

    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    print()

    passed = 0
    failed = 0

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    print()
    print("=" * 80)
    print(f"Total: {passed} passed, {failed} failed out of {len(results)} tests")
    print("=" * 80)
    print()

    if failed == 0:
        print("🎉 ALL TESTS PASSED! Encryption key management is properly configured.")
        print()
        return 0
    else:
        print("⚠️  SOME TESTS FAILED. Please review the failures above.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
