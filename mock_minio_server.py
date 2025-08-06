
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI(title="Mock MinIO Object Storage", version="1.0.0")

@app.get("/minio/health/live")
async def health_check():
    return {"status": "healthy", "service": "minio"}

@app.get("/")
async def root():
    return {"message": "🗄️ Mock MinIO Object Storage - Ready"}

@app.get("/admin/v3/info")
async def admin_info():
    return {
        "mode": "standalone",
        "deploymentID": "iris-minio-deployment",
        "region": "us-east-1",
        "buckets": {"count": 0}
    }

if __name__ == "__main__":
    print("🗄️ Starting Mock MinIO Object Storage...")
    print("🌐 Access: http://localhost:9000")
    uvicorn.run(app, host="0.0.0.0", port=9000)
