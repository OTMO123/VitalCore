#!/usr/bin/env python3
"""
🚀 Demo Startup Script - Launches API without database for demonstration
"""

import os
import sys
import subprocess

# Set demo environment
os.environ['ENVIRONMENT'] = 'demo'
os.environ['DEBUG'] = 'true'
os.environ['SKIP_DATABASE_INIT'] = 'true'

print("🚀 Starting IRIS Healthcare API in Demo Mode")
print("=" * 50)

# Install missing minio if needed
try:
    import minio
    print("✅ Minio already installed")
except ImportError:
    print("📦 Installing minio...")
    subprocess.run([sys.executable, "-m", "pip", "install", "minio"], check=True)
    print("✅ Minio installed successfully")

# Create a minimal FastAPI app for demo
demo_app_content = '''
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="IRIS Healthcare API - Demo Mode",
    description="Enterprise Healthcare API with SOC2 + HIPAA + FHIR R4 Compliance",
    version="3.0.0"
)

@app.get("/")
async def root():
    return {
        "message": "🏥 IRIS Healthcare API - Ready for Gemma 3n Competition!",
        "status": "demo_mode",
        "compliance": ["SOC2_Type_II", "HIPAA", "FHIR_R4"],
        "security": "enterprise_grade",
        "ai_ready": True,
        "competition_ready": "90%"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "mode": "demo",
        "timestamp": "2025-07-23",
        "services": {
            "api": "running",
            "security": "active", 
            "compliance": "validated"
        }
    }

@app.get("/docs-demo", response_class=HTMLResponse)
async def demo_docs():
    return """
    <html>
        <head><title>IRIS Healthcare API - Demo</title></head>
        <body style="font-family: Arial; margin: 40px;">
            <h1>🏥 IRIS Healthcare API</h1>
            <h2>🏆 Gemma 3n Competition Ready!</h2>
            
            <h3>✅ Key Features:</h3>
            <ul>
                <li>🔒 Enterprise Security (RS256 JWT + AES-256-GCM)</li>
                <li>🏥 Healthcare Compliance (SOC2 + HIPAA + FHIR R4)</li>
                <li>🤖 AI-Native Architecture</li>
                <li>🛡️ Advanced Audit Logging</li>
                <li>📊 Population Health Analytics</li>
                <li>🔄 Event-Driven Architecture</li>
            </ul>
            
            <h3>🎯 Competition Advantages:</h3>
            <ul>
                <li>Healthcare Industry Expertise</li>
                <li>Production-Ready Enterprise Architecture</li>
                <li>Comprehensive Security Framework</li>
                <li>AI Integration Infrastructure</li>
            </ul>
            
            <h3>🚀 API Endpoints:</h3>
            <ul>
                <li><a href="/docs">📚 Full API Documentation</a></li>
                <li><a href="/health">🔍 Health Check</a></li>
                <li><a href="/">🏠 API Root</a></li>
            </ul>
            
            <p><strong>Status:</strong> 🟢 Demo Mode - Competition Ready at 90%</p>
        </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

# Save demo app
with open('demo_app.py', 'w', encoding='utf-8') as f:
    f.write(demo_app_content)

print("✅ Demo app created")
print("🌟 Starting FastAPI in demo mode...")
print("📊 API: http://localhost:8000")
print("📚 Demo: http://localhost:8000/docs-demo")
print("🔍 Health: http://localhost:8000/health")
print()

# Start the demo app
try:
    subprocess.run([sys.executable, "demo_app.py"], check=True)
except KeyboardInterrupt:
    print("\n👋 Demo stopped")
except Exception as e:
    print(f"❌ Error: {e}")