#!/usr/bin/env python3
"""
Test runner with PostgreSQL backend.
Falls back to SQLite if PostgreSQL is not available.
"""
import asyncio
import sys
import os
import subprocess

# Add project root to path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def check_postgresql_available():
    """Check if PostgreSQL is running and accessible."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='iris_db',
            user='postgres',
            password='password',
            connect_timeout=5
        )
        conn.close()
        return True
    except Exception as e:
        print(f"PostgreSQL not available: {e}")
        return False

def start_docker_services():
    """Attempt to start Docker services."""
    try:
        print("Starting Docker services...")
        result = subprocess.run(
            ["docker-compose", "up", "-d", "db", "redis"],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print("Docker services started successfully")
            # Wait a bit for services to be ready
            import time
            time.sleep(10)
            return True
        else:
            print(f"Docker startup failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("Docker startup timed out")
        return False
    except FileNotFoundError:
        print("Docker not available")
        return False
    except Exception as e:
        print(f"Docker startup error: {e}")
        return False

def apply_migrations():
    """Apply database migrations."""
    try:
        print("Applying database migrations...")
        result = subprocess.run([
            "venv/Scripts/alembic.exe" if os.name == 'nt' else "venv/bin/alembic",
            "upgrade", "head"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Migrations applied successfully")
            return True
        else:
            print(f"Migration failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"Migration error: {e}")
        return False

async def test_with_postgresql():
    """Run tests with PostgreSQL backend."""
    print("\n" + "=" * 70)
    print("RUNNING TESTS WITH POSTGRESQL BACKEND")
    print("=" * 70)
    
    try:
        # Import test modules
        from test_with_sqlite import (
            test_database_operations,
            test_encryption_service,
            test_fastapi_app,
            test_event_bus,
            test_healthcare_modules
        )
        
        # Override database URL for PostgreSQL
        os.environ['DATABASE_URL'] = 'postgresql+asyncpg://postgres:password@localhost:5432/iris_db'
        
        test_functions = [
            test_database_operations,
            test_encryption_service,
            test_fastapi_app,
            test_event_bus,
            test_healthcare_modules,
        ]
        
        passed = 0
        failed = 0
        
        for test_func in test_functions:
            try:
                print(f"\n--- Running {test_func.__name__} with PostgreSQL ---")
                result = await test_func()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"[FAIL] {test_func.__name__} crashed: {e}")
                failed += 1
        
        print("\n" + "=" * 70)
        print(f"POSTGRESQL TEST RESULTS: {passed} passed, {failed} failed")
        print("=" * 70)
        
        return failed == 0
        
    except Exception as e:
        print(f"PostgreSQL testing failed: {e}")
        return False

async def test_with_sqlite_fallback():
    """Fallback to SQLite testing."""
    print("\n" + "=" * 70)
    print("FALLBACK: RUNNING TESTS WITH SQLITE")
    print("=" * 70)
    
    try:
        from test_with_sqlite import run_comprehensive_tests
        return await run_comprehensive_tests()
    except Exception as e:
        print(f"SQLite fallback failed: {e}")
        return False

def run_pytest_smoke_tests():
    """Run official pytest smoke tests."""
    print("\n" + "=" * 70)
    print("RUNNING OFFICIAL PYTEST SMOKE TESTS")
    print("=" * 70)
    
    try:
        result = subprocess.run([
            "venv/Scripts/pytest.exe" if os.name == 'nt' else "venv/bin/pytest",
            "app/tests/smoke/test_basic.py",
            "-v", "--tb=short"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Pytest execution failed: {e}")
        return False

async def main():
    """Main test runner with multiple strategies."""
    print("IRIS API COMPREHENSIVE TEST RUNNER")
    print("=" * 70)
    
    # Strategy 1: Try PostgreSQL with Docker
    postgresql_available = False
    if check_postgresql_available():
        postgresql_available = True
        print("[OK] PostgreSQL already running")
    else:
        print("[INFO] PostgreSQL not running, attempting to start Docker services...")
        if start_docker_services():
            if check_postgresql_available():
                if apply_migrations():
                    postgresql_available = True
                    print("[OK] PostgreSQL ready with migrations")
                else:
                    print("[WARN] PostgreSQL running but migrations failed")
            else:
                print("[WARN] Docker started but PostgreSQL not accessible")
        else:
            print("[INFO] Docker services not available")
    
    results = []
    
    # Run PostgreSQL tests if available
    if postgresql_available:
        try:
            pg_result = await test_with_postgresql()
            results.append(("PostgreSQL Tests", pg_result))
        except Exception as e:
            print(f"PostgreSQL testing crashed: {e}")
            results.append(("PostgreSQL Tests", False))
    
    # Always run SQLite tests as baseline
    try:
        sqlite_result = await test_with_sqlite_fallback()
        results.append(("SQLite Tests", sqlite_result))
    except Exception as e:
        print(f"SQLite testing crashed: {e}")
        results.append(("SQLite Tests", False))
    
    # Run pytest smoke tests
    try:
        pytest_result = run_pytest_smoke_tests()
        results.append(("Pytest Smoke Tests", pytest_result))
    except Exception as e:
        print(f"Pytest testing crashed: {e}")
        results.append(("Pytest Smoke Tests", False))
    
    # Summary
    print("\n" + "=" * 70)
    print("FINAL TEST SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for test_name, passed in results:
        status = "PASSED" if passed else "FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\nSUCCESS: All available tests passed!")
        print("Your IRIS API system is ready for development.")
    else:
        print("\nWARNING: Some tests failed. Check output above.")
    
    return all_passed

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTesting interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Test runner failed: {e}")
        sys.exit(1)