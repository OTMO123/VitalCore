#!/usr/bin/env python3
"""
VitalCore Encryption Key Generator

CRITICAL SECURITY TOOL: Generate secure encryption keys for PHI data protection.

⚠️  WARNING: Loss of encryption keys = PERMANENT DATA LOSS
⚠️  Store these keys securely in a password manager or secrets vault
⚠️  NEVER commit these keys to version control
⚠️  Back up keys in multiple secure locations

Usage:
    python scripts/generate_encryption_keys.py

The script will generate:
- PRIMARY PHI encryption key (32-byte base64 urlsafe)
- ENCRYPTION_KEY (32-byte base64 urlsafe)
- ENCRYPTION_SALT (32-byte base64 urlsafe)
- JWT_SECRET_KEY (32-byte base64 urlsafe)
- SECRET_KEY (32-byte base64 urlsafe)
- PHI_ENCRYPTION_KEY_ROTATION (optional, for key rotation)

For HIPAA compliance and production deployment.
"""

import secrets
import sys
from datetime import datetime


def generate_secure_key(length: int = 32) -> str:
    """
    Generate a cryptographically secure random key.

    Args:
        length: Length of the key in bytes (default: 32 for 256-bit security)

    Returns:
        Base64 URL-safe encoded key string
    """
    return secrets.token_urlsafe(length)


def print_banner():
    """Print security banner with critical warnings."""
    print("=" * 80)
    print("🔐 VITALCORE ENCRYPTION KEY GENERATOR")
    print("=" * 80)
    print()
    print("⚠️  CRITICAL SECURITY WARNINGS:")
    print("   • These keys protect PHI (Protected Health Information)")
    print("   • Loss of these keys = PERMANENT DATA LOSS")
    print("   • NEVER commit these keys to version control")
    print("   • Store keys in a secure password manager or secrets vault")
    print("   • Back up keys in multiple secure, offline locations")
    print("   • Rotate keys periodically (use PHI_ENCRYPTION_KEY_ROTATION)")
    print()
    print("=" * 80)
    print()


def generate_all_keys():
    """Generate all required encryption keys for VitalCore."""
    # Generate all keys
    phi_encryption_key = generate_secure_key(32)
    encryption_key = generate_secure_key(32)
    encryption_salt = generate_secure_key(32)
    jwt_secret_key = generate_secure_key(32)
    secret_key = generate_secure_key(32)
    phi_rotation_key = generate_secure_key(32)

    return {
        "PHI_ENCRYPTION_KEY": phi_encryption_key,
        "ENCRYPTION_KEY": encryption_key,
        "ENCRYPTION_SALT": encryption_salt,
        "JWT_SECRET_KEY": jwt_secret_key,
        "SECRET_KEY": secret_key,
        "PHI_ENCRYPTION_KEY_ROTATION": phi_rotation_key,
    }


def print_env_format(keys: dict):
    """Print keys in .env file format."""
    print("📄 ENVIRONMENT VARIABLES (.env format)")
    print("=" * 80)
    print()
    print("# Copy these lines to your .env file")
    print("# DO NOT use these keys in production - generate new ones for each environment")
    print()
    print("# ============================================================================")
    print("# CRITICAL: ENCRYPTION KEYS FOR PHI DATA PROTECTION")
    print("# ============================================================================")
    print("# ⚠️  WARNING: These keys MUST persist across application restarts!")
    print("# ⚠️  Loss of these keys = permanent loss of ALL encrypted PHI data")
    print("# ⚠️  Store these keys securely - NEVER commit to version control")
    print(f"# Generated: {datetime.utcnow().isoformat()}Z")
    print("# ============================================================================")
    print()
    print("# Primary PHI Encryption Key (REQUIRED - 32+ characters)")
    print(f"PHI_ENCRYPTION_KEY={keys['PHI_ENCRYPTION_KEY']}")
    print()
    print("# Encryption Key for data at rest (REQUIRED - 32+ characters)")
    print(f"ENCRYPTION_KEY={keys['ENCRYPTION_KEY']}")
    print()
    print("# Encryption Salt for key derivation (REQUIRED - 32+ characters)")
    print(f"ENCRYPTION_SALT={keys['ENCRYPTION_SALT']}")
    print()
    print("# JWT Signing Key (REQUIRED - 32+ characters)")
    print(f"JWT_SECRET_KEY={keys['JWT_SECRET_KEY']}")
    print()
    print("# Application Secret Key (REQUIRED - 32+ characters)")
    print(f"SECRET_KEY={keys['SECRET_KEY']}")
    print()
    print("# PHI Encryption Key Rotation (OPTIONAL - for key rotation support)")
    print(f"PHI_ENCRYPTION_KEY_ROTATION={keys['PHI_ENCRYPTION_KEY_ROTATION']}")
    print()
    print("=" * 80)
    print()


def print_security_instructions():
    """Print security best practices and next steps."""
    print("🔒 SECURITY BEST PRACTICES")
    print("=" * 80)
    print()
    print("1. IMMEDIATE ACTIONS:")
    print("   ✓ Copy the keys above to your .env file")
    print("   ✓ Store a backup copy in a secure password manager (1Password, LastPass, etc.)")
    print("   ✓ Store an offline backup in a secure physical location")
    print("   ✓ Ensure .env is listed in .gitignore")
    print()
    print("2. PRODUCTION DEPLOYMENT:")
    print("   ✓ Use environment variables (not .env files) in production")
    print("   ✓ Use a secrets management service (AWS Secrets Manager, HashiCorp Vault)")
    print("   ✓ Enable automated key rotation with PHI_ENCRYPTION_KEY_ROTATION")
    print("   ✓ Implement key access auditing")
    print()
    print("3. KEY ROTATION PROCEDURE:")
    print("   ✓ Generate new keys using this script")
    print("   ✓ Set new key as PHI_ENCRYPTION_KEY_ROTATION")
    print("   ✓ Run key rotation migration script (to be implemented)")
    print("   ✓ Update PHI_ENCRYPTION_KEY to rotation key")
    print("   ✓ Generate new rotation key")
    print()
    print("4. DISASTER RECOVERY:")
    print("   ✓ Test key backup and restore procedures quarterly")
    print("   ✓ Document key recovery procedures")
    print("   ✓ Maintain encrypted backups of the database")
    print("   ✓ Test decryption with backup keys")
    print()
    print("5. COMPLIANCE REQUIREMENTS:")
    print("   ✓ HIPAA: Keys must be protected as electronic PHI")
    print("   ✓ SOC2: Document key management procedures")
    print("   ✓ GDPR: Implement key access controls and logging")
    print("   ✓ Audit key access and usage regularly")
    print()
    print("=" * 80)
    print()
    print("📚 DOCUMENTATION:")
    print("   • See docs/ENCRYPTION_KEY_SETUP.md for detailed setup instructions")
    print("   • See docs/DISASTER_RECOVERY.md for recovery procedures")
    print()
    print("=" * 80)


def print_docker_format(keys: dict):
    """Print keys in docker-compose.yml format."""
    print()
    print("🐳 DOCKER COMPOSE FORMAT")
    print("=" * 80)
    print()
    print("# Add these to your docker-compose.yml environment section:")
    print()
    print("    environment:")
    print(f"      - PHI_ENCRYPTION_KEY={keys['PHI_ENCRYPTION_KEY']}")
    print(f"      - ENCRYPTION_KEY={keys['ENCRYPTION_KEY']}")
    print(f"      - ENCRYPTION_SALT={keys['ENCRYPTION_SALT']}")
    print(f"      - JWT_SECRET_KEY={keys['JWT_SECRET_KEY']}")
    print(f"      - SECRET_KEY={keys['SECRET_KEY']}")
    print(f"      - PHI_ENCRYPTION_KEY_ROTATION={keys['PHI_ENCRYPTION_KEY_ROTATION']}")
    print()
    print("=" * 80)


def main():
    """Main function to generate and display encryption keys."""
    print_banner()

    # Get user confirmation
    print("⚠️  This will generate NEW encryption keys.")
    print("⚠️  Only use for NEW deployments or key rotation.")
    print("⚠️  Using new keys on existing encrypted data will cause DATA LOSS!")
    print()
    response = input("Continue? (type 'YES' to confirm): ")

    if response.strip() != "YES":
        print()
        print("❌ Key generation cancelled.")
        print()
        sys.exit(0)

    print()
    print("🔑 Generating cryptographically secure keys...")
    print()

    # Generate keys
    keys = generate_all_keys()

    # Print keys in various formats
    print_env_format(keys)
    print_docker_format(keys)
    print_security_instructions()

    print("✅ Encryption keys generated successfully!")
    print()
    print("⚠️  REMEMBER: Store these keys securely in multiple locations!")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print()
        print("❌ Key generation cancelled by user.")
        print()
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ ERROR: {str(e)}")
        print()
        sys.exit(1)
