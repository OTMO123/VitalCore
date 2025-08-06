#!/usr/bin/env python3
"""
VitalCore Frontend Server
Simple HTTP server for development
"""
import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

def start_frontend_server(port=3000):
    """Start a simple HTTP server for the frontend"""
    
    # Change to frontend directory
    frontend_dir = Path(__file__).parent / "frontend"
    
    if not frontend_dir.exists():
        frontend_dir.mkdir(exist_ok=True)
        print(f"Created frontend directory: {frontend_dir}")
    
    os.chdir(frontend_dir)
    
    # Create a simple handler that serves files
    class CustomHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            # Add CORS headers for API calls
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            super().end_headers()
        
        def do_OPTIONS(self):
            # Handle preflight requests
            self.send_response(200)
            self.end_headers()
    
    # Start the server
    with socketserver.TCPServer(("", port), CustomHandler) as httpd:
        print(f"🚀 VitalCore Frontend Server starting...")
        print(f"📱 Server running at: http://localhost:{port}")
        print(f"🏥 VitalCore App: http://localhost:{port}/components/core/VitalCore.html")
        print(f"🩺 Healthcare App: http://localhost:{port}/components/core/HealthcareApp.html")
        print(f"📊 API Client: http://localhost:{port}/api/vitalcore-client.js")
        print(f"\n💡 Make sure your backend is running at http://localhost:8000")
        print(f"🔧 Backend command: python run.py")
        print(f"\n❌ Press Ctrl+C to stop the server")
        
        # Auto-open browser
        try:
            webbrowser.open(f"http://localhost:{port}/components/core/VitalCore.html")
        except Exception as e:
            print(f"Could not auto-open browser: {e}")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n🛑 VitalCore Frontend Server stopped")
            sys.exit(0)

if __name__ == "__main__":
    port = 3000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number, using default 3000")
    
    start_frontend_server(port)