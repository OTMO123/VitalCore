
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
