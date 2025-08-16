#!/usr/bin/env python3
"""
Simple Database Connection Test

Tests if we can connect to the running PostgreSQL database.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_database_connection():
    """Test basic database connectivity."""
    print("🗄️ Testing Database Connection...")
    
    try:
        # Try to import required modules
        try:
            import asyncio
            import asyncpg
            print("   ✅ Required modules available")
        except ImportError as e:
            print(f"   ❌ Missing modules: {e}")
            return False
        
        # Test direct PostgreSQL connection
        async def connect_test():
            try:
                # Connect to the database directly
                conn = await asyncpg.connect(
                    host='localhost',
                    port=5432,
                    user='postgres',
                    password='postgres',
                    database='iris_healthcare'
                )
                
                # Simple query test
                result = await conn.fetchval('SELECT 1')
                assert result == 1
                
                print("   ✅ PostgreSQL connection successful")
                
                # Check if tables exist
                tables = await conn.fetch("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                
                table_names = [table['table_name'] for table in tables]
                print(f"   📋 Found {len(table_names)} tables: {table_names[:5]}...")
                
                await conn.close()
                return True
                
            except Exception as e:
                print(f"   ❌ PostgreSQL connection failed: {e}")
                return False
        
        # Run the async test
        return asyncio.run(connect_test())
        
    except Exception as e:
        print(f"   ❌ Database connection test failed: {e}")
        return False

def test_api_connectivity():
    """Test API connectivity."""
    print("\n🌐 Testing API Connection...")
    
    try:
        import requests
        
        # Test health endpoint
        response = requests.get('http://localhost:8000/health', timeout=5)
        
        if response.status_code == 200:
            print("   ✅ API health check successful")
            health_data = response.json()
            print(f"   📊 API Status: {health_data.get('status', 'unknown')}")
            return True
        else:
            print(f"   ❌ API health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ API connection test failed: {e}")
        return False

def main():
    """Run connectivity tests."""
    print("🔍 INFRASTRUCTURE CONNECTIVITY TEST")
    print("=" * 50)
    
    db_ok = test_database_connection()
    api_ok = test_api_connectivity()
    
    print("\n" + "=" * 50)
    print("📊 CONNECTIVITY TEST SUMMARY:")
    print(f"   Database: {'✅ Connected' if db_ok else '❌ Failed'}")
    print(f"   API: {'✅ Connected' if api_ok else '❌ Failed'}")
    
    if db_ok and api_ok:
        print("\n🎉 All infrastructure connectivity tests passed!")
        print("✅ Ready for enterprise functionality testing")
        return True
    else:
        print("\n⚠️  Some connectivity tests failed")
        print("❌ Infrastructure needs attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)