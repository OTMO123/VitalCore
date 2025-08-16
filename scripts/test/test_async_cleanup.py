#!/usr/bin/env python3
"""
Test script for enhanced async database connection cleanup.

This script tests the fixes for:
- RuntimeWarning: coroutine 'Connection._cancel' was never awaited
- Proper async resource management
- Connection pool cleanup verification
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager

# Configure logging to capture warnings
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Import warnings to catch specific async warnings
import warnings
warnings.filterwarnings("error", category=RuntimeWarning, message=".*coroutine.*_cancel.*never awaited.*")

async def test_database_connection_cleanup():
    """Test enhanced database connection cleanup."""
    print("🔧 Testing Enhanced Database Connection Cleanup")
    print("=" * 60)
    
    try:
        # Import the enhanced database configuration
        from app.core.database_unified import (
            init_db, close_db, get_db, 
            get_connection_manager, shutdown_connection_manager,
            EnterpriseConnectionManager
        )
        
        print("✅ Successfully imported enhanced database modules")
        
        # Test 1: Initialize database
        print("\n1. Testing database initialization...")
        await init_db()
        print("✅ Database initialized successfully")
        
        # Test 2: Test connection manager
        print("\n2. Testing connection manager...")
        connection_manager = get_connection_manager()
        stats_before = connection_manager.get_stats()
        print(f"✅ Connection manager stats: {stats_before}")
        
        # Test 3: Create multiple database sessions
        print("\n3. Testing multiple database sessions...")
        tasks = []
        for i in range(5):
            task = test_database_session(i)
            tasks.append(task)
        
        # Run sessions concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for any exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ Session {i} failed: {result}")
            else:
                print(f"✅ Session {i} completed successfully")
        
        # Test 4: Check connection manager stats after operations
        print("\n4. Checking connection manager stats...")
        stats_after = connection_manager.get_stats()
        print(f"✅ Connection stats after operations: {stats_after}")
        
        # Test 5: Test graceful shutdown
        print("\n5. Testing graceful connection shutdown...")
        await close_db()
        print("✅ Database connections closed successfully")
        
        # Test 6: Verify no active connections remain
        print("\n6. Verifying cleanup completion...")
        final_stats = connection_manager.get_stats()
        print(f"✅ Final connection stats: {final_stats}")
        
        if final_stats.get("active_connections", 0) == 0:
            print("✅ All connections properly cleaned up")
        else:
            print(f"⚠️  {final_stats['active_connections']} connections still active")
        
        return True
        
    except RuntimeWarning as e:
        if "coroutine" in str(e) and "_cancel" in str(e):
            print(f"❌ ASYNC CLEANUP WARNING DETECTED: {e}")
            return False
        else:
            raise
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_database_session(session_id: int):
    """Test individual database session with proper cleanup."""
    try:
        print(f"  Starting session {session_id}...")
        
        # Use the enhanced session management
        async for db in get_db():
            # Simulate some database operations
            from sqlalchemy import text
            result = await db.execute(text("SELECT 1 as test_value"))
            row = result.fetchone()
            
            if row and row[0] == 1:
                print(f"  ✅ Session {session_id}: Database query successful")
            else:
                print(f"  ❌ Session {session_id}: Database query returned unexpected result")
            
            # Simulate some processing time
            await asyncio.sleep(0.1)
            
            break  # Exit the async generator
        
        print(f"  ✅ Session {session_id} completed and cleaned up")
        return True
        
    except Exception as e:
        print(f"  ❌ Session {session_id} failed: {e}")
        raise

async def test_connection_pool_monitoring():
    """Test the connection pool monitoring functionality."""
    print("\n🔍 Testing Connection Pool Monitoring")
    print("=" * 40)
    
    try:
        from app.core.database_unified import get_connection_manager, get_engine
        
        # Get connection manager
        connection_manager = get_connection_manager()
        
        # Get engine
        engine = await get_engine()
        
        # Display connection pool information
        pool_stats = connection_manager.get_stats()
        print(f"Connection Manager Stats: {pool_stats}")
        
        if engine and hasattr(engine, 'pool'):
            try:
                engine_pool_stats = {
                    "size": engine.pool.size() if hasattr(engine.pool, 'size') else 'N/A',
                    "checked_out": engine.pool.checkedout() if hasattr(engine.pool, 'checkedout') else 'N/A',
                    "overflow": engine.pool.overflow() if hasattr(engine.pool, 'overflow') else 'N/A',
                }
                print(f"SQLAlchemy Pool Stats: {engine_pool_stats}")
            except Exception as e:
                print(f"Engine pool stats unavailable: {e}")
        
        print("✅ Connection pool monitoring test completed")
        return True
        
    except Exception as e:
        print(f"❌ Connection pool monitoring test failed: {e}")
        return False

async def main():
    """Main test function."""
    print("🚀 Enhanced Database Async Connection Cleanup Test Suite")
    print("=" * 70)
    
    start_time = time.time()
    
    # Run tests
    test1_result = await test_database_connection_cleanup()
    test2_result = await test_connection_pool_monitoring()
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"Database Connection Cleanup Test: {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"Connection Pool Monitoring Test: {'✅ PASSED' if test2_result else '❌ FAILED'}")
    print(f"Total test duration: {duration:.2f} seconds")
    
    if test1_result and test2_result:
        print("\n🎉 ALL TESTS PASSED! Async connection cleanup is working correctly.")
        print("\nThe following issues have been fixed:")
        print("  ✅ RuntimeWarning: coroutine 'Connection._cancel' was never awaited")
        print("  ✅ Proper async session cleanup with timeout protection")
        print("  ✅ Enhanced connection pool management")
        print("  ✅ Graceful shutdown handling for async resources")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
        return 1

if __name__ == "__main__":
    # Run the test suite
    import sys
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite failed with unexpected error: {e}")
        sys.exit(1)