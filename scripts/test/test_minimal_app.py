#!/usr/bin/env python3
"""
Minimal FastAPI app to test middleware.
"""

from fastapi import FastAPI

# Create minimal app
app = FastAPI(title="Test App")

@app.middleware("http")
async def test_middleware(request, call_next):
    print(f"MINIMAL MIDDLEWARE WORKS: {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"MINIMAL RESPONSE: {response.status_code}")
    return response

@app.get("/")
async def root():
    return {"message": "Minimal app works"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/test")
async def test_post():
    return {"message": "POST works"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)