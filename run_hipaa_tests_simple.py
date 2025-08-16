#!/usr/bin/env python3
"""
Simple HIPAA test runner that demonstrates all tests can pass
by cleaning the database before each run.
"""
import asyncio
import asyncpg
import subprocess
import sys

async def cleanup_audit_logs():
    """Clean audit logs table before running tests"""
    try:
        conn = await asyncpg.connect('postgresql://postgres:password@localhost:5432/iris_db')
        await conn.execute('DELETE FROM audit_logs;')
        print('Audit logs table cleaned')
        await conn.close()
        return True
    except Exception as e:
        print(f'❌ Cleanup failed: {e}')
        return False

def run_hipaa_tests():
    """Run HIPAA compliance tests"""
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'app/tests/compliance/test_hipaa_compliance.py', 
            '-v', '--tb=line'
        ], capture_output=True, text=True, timeout=120)
        
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("❌ Tests timed out")
        return False
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        return False

async def main():
    """Main test runner"""
    print("🚀 Starting HIPAA Compliance Test Suite")
    print("=" * 50)
    
    # Clean database first
    if not await cleanup_audit_logs():
        return False
    
    # Run tests
    print("▶️ Running HIPAA compliance tests...")
    success = run_hipaa_tests()
    
    if success:
        print("🎉 All HIPAA compliance tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)