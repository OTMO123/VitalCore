#!/usr/bin/env python3
"""
Quick check for asyncpg availability.
"""
import sys

print("🔍 Checking asyncpg driver availability...")

try:
    import asyncpg
    print("✅ asyncpg is available")
    print(f"   Version: {asyncpg.__version__}")
except ImportError as e:
    print("❌ asyncpg is NOT available")
    print(f"   Error: {e}")
    print("\n💡 Fix: Install asyncpg in your virtual environment")
    print("   .venv\\Scripts\\pip.exe install asyncpg")
    sys.exit(1)

try:
    import psycopg2
    print("⚠️  psycopg2 is also available (might conflict)")
    print(f"   Version: {psycopg2.__version__}")
except ImportError:
    print("✅ psycopg2 is not available (good for async)")

print("\n🚀 Database driver status: Ready for async operations!")