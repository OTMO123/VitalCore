#!/usr/bin/env python3
"""
Direct FastAPI test without uvicorn.
"""

import asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Create test app
app = FastAPI()

middleware_called = False

@app.middleware("http")
async def debug_middleware(request, call_next):
    global middleware_called
    middleware_called = True
    print(f"DIRECT TEST MIDDLEWARE: {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"DIRECT TEST RESPONSE: {response.status_code}")
    return response

@app.get("/")
async def root():
    return {"message": "Direct test works"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

def test_direct_fastapi():
    """Test FastAPI directly with TestClient."""
    global middleware_called
    
    print("TESTING FASTAPI DIRECTLY")
    print("=" * 40)
    
    # Create test client
    client = TestClient(app)
    
    # Test root endpoint
    print("Testing GET /")
    response = client.get("/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print(f"Middleware called: {middleware_called}")
    
    # Reset flag
    middleware_called = False
    
    # Test health endpoint
    print("\nTesting GET /health")
    response = client.get("/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print(f"Middleware called: {middleware_called}")
    
    print(f"\nFinal check - middleware should have been called!")

if __name__ == "__main__":
    test_direct_fastapi()