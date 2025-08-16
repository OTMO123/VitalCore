#!/usr/bin/env python3
"""
Simple test to verify pytest is working without database dependencies.
"""
import pytest


def test_basic_math():
    """Test basic arithmetic to verify pytest works."""
    assert 2 + 2 == 4
    assert 10 - 5 == 5
    assert 3 * 4 == 12


def test_string_operations():
    """Test string operations."""
    text = "Hello World"
    assert text.lower() == "hello world"
    assert text.upper() == "HELLO WORLD"
    assert len(text) == 11


@pytest.mark.asyncio
async def test_async_function():
    """Test async function works."""
    async def async_add(a, b):
        return a + b
    
    result = await async_add(5, 3)
    assert result == 8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])