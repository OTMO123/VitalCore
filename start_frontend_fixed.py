#!/usr/bin/env python3
"""
VitalCore Frontend Server - Fixed Version
Simple HTTP server for development with port collision handling
"""
import http.server
import socketserver
import webbrowser
import os
import sys
import socket
from pathlib import Path

def find_free_port(start_port=5173, max_port=5200):
    """Find a free port starting from start_port"""
    for port in range(start_port, max_port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            result = sock.bind(('', port))
            sock.close()
            return port
        except OSError:
            continue
    raise RuntimeError(f"No free port found between {start_port} and {max_port}")

def start_frontend_server(preferred_port=5173):
    """Start a simple HTTP server for the frontend"""
    
    # Change to frontend directory
    frontend_dir = Path(__file__).parent / "frontend"
    
    if not frontend_dir.exists():
        frontend_dir.mkdir(exist_ok=True)
        print(f"Created frontend directory: {frontend_dir}")
    
    os.chdir(frontend_dir)
    
    # Find a free port
    try:
        port = find_free_port(preferred_port)
        if port != preferred_port:
            print(f"⚠️  Port {preferred_port} is busy, using port {port} instead")
    except RuntimeError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
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
        
        def log_message(self, format, *args):
            # Suppress default logging for cleaner output
            pass
    
    # Start the server
    try:
        with socketserver.TCPServer(("", port), CustomHandler) as httpd:
            print(f"🚀 VitalCore Frontend Server starting...")
            print(f"📱 Server running at: http://localhost:{port}")
            print(f"🏥 VitalCore App: http://localhost:{port}/components/core/VitalCore.html")
            print(f"🏥 Production App: http://localhost:{port}/components/core/VitalCore-Production.html")
            print(f"🩺 Healthcare App: http://localhost:{port}/components/core/HealthcareApp.html")
            print(f"📊 API Client: http://localhost:{port}/api/vitalcore-client.js")
            print(f"\n💡 Make sure your backend is running at http://localhost:8000")
            print(f"🔧 Backend command: python run.py")
            print(f"\n❌ Press Ctrl+C to stop the server")
            print(f"{'='*60}")
            
            # Auto-open browser to production version
            try:
                production_url = f"http://localhost:{port}/components/core/VitalCore-Production.html"
                print(f"🌐 Opening browser: {production_url}")
                webbrowser.open(production_url)
            except Exception as e:
                print(f"Could not auto-open browser: {e}")
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print(f"\n🛑 VitalCore Frontend Server stopped")
                sys.exit(0)
                
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is still in use. Try a different port:")
            print(f"   python start_frontend_fixed.py {port + 1}")
        else:
            print(f"❌ Failed to start server: {e}")
        sys.exit(1)

def kill_process_on_port(port):
    """Kill any process using the specified port (Windows)"""
    try:
        import subprocess
        # Find process using the port
        result = subprocess.run(
            ['netstat', '-ano'], 
            capture_output=True, 
            text=True, 
            shell=True
        )
        
        for line in result.stdout.split('\n'):
            if f':{port}' in line and 'LISTENING' in line:
                # Extract PID
                parts = line.strip().split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    print(f"🔍 Found process {pid} using port {port}")
                    
                    # Kill the process
                    subprocess.run(['taskkill', '/PID', pid, '/F'], shell=True)
                    print(f"✅ Killed process {pid}")
                    return True
                    
    except Exception as e:
        print(f"⚠️  Could not kill process on port {port}: {e}")
        return False
    
    return False

if __name__ == "__main__":
    port = 5173
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--kill":
            # Kill any process using port 5173
            kill_process_on_port(5173)
            sys.exit(0)
        else:
            try:
                port = int(sys.argv[1])
            except ValueError:
                print("Invalid port number, using default 3000")
    
    print("🎯 Starting VitalCore Frontend Server...")
    start_frontend_server(port)