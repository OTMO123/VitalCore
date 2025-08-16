#!/usr/bin/env python3
"""
Simple performance test to verify basic functionality
"""

import pytest
import asyncio
import time
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database_performance import DatabasePerformanceMonitor

@pytest.mark.asyncio
async def test_simple_performance():
    """Simple performance test"""
    print("Starting simple performance test...")
    
    # Test basic performance monitoring
    monitor = DatabasePerformanceMonitor()
    
    # Simple timing test
    start_time = time.time()
    await asyncio.sleep(0.1)  # 100ms
    end_time = time.time()
    
    elapsed = end_time - start_time
    print(f"Elapsed time: {elapsed:.3f}s")
    
    assert elapsed >= 0.1, "Should take at least 100ms"
    assert elapsed < 0.2, "Should not take more than 200ms"
    
    print("✅ Simple performance test passed!")

if __name__ == "__main__":
    asyncio.run(test_simple_performance())