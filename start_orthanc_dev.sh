#!/bin/bash
# 🏥 Start IRIS Orthanc Development Environment

echo "🚀 Starting IRIS Healthcare - Orthanc DICOM Integration"
echo "=================================================="

# Start Mock Orthanc in background
echo "🏥 Starting Mock Orthanc DICOM Server..."
python3 mock_orthanc_server.py &
ORTHANC_PID=$!

# Start Mock MinIO in background  
echo "🗄️ Starting Mock MinIO Object Storage..."
python3 mock_minio_server.py &
MINIO_PID=$!

echo ""
echo "✅ Services Started:"
echo "🏥 Orthanc DICOM: http://localhost:8042"
echo "🗄️ MinIO Storage: http://localhost:9000"
echo ""
echo "🔑 Orthanc Credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo "   API User: iris_api"
echo "   API Key: secure_iris_key_2024"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "echo 'Stopping services...'; kill $ORTHANC_PID $MINIO_PID 2>/dev/null; exit" INT
wait
