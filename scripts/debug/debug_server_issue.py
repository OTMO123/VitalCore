#!/usr/bin/env python3
"""
Debug server connection issue.
"""

import urllib.request
import urllib.parse
import socket
import json

def check_port_8000():
    """Check what's running on port 8000."""
    print("CHECKING PORT 8000")
    print("=" * 30)
    
    try:
        # Try to connect to port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()
        
        if result == 0:
            print("Port 8000 is OPEN")
        else:
            print("Port 8000 is CLOSED")
            
    except Exception as e:
        print(f"Socket check error: {e}")

def test_different_endpoints():
    """Test different endpoints to see response patterns."""
    print("\nTESTING ENDPOINTS")
    print("=" * 30)
    
    endpoints = [
        "/health",
        "/",
        "/docs",
        "/api/v1/auth/login",
        "/nonexistent"
    ]
    
    for endpoint in endpoints:
        url = f"http://localhost:8000{endpoint}"
        try:
            if endpoint == "/api/v1/auth/login":
                # POST request
                data = urllib.parse.urlencode({'username': 'admin', 'password': 'admin123'}).encode()
                headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            else:
                # GET request
                req = urllib.request.Request(url, method='GET')
            
            with urllib.request.urlopen(req) as response:
                print(f"✅ {endpoint}: {response.status}")
                
        except urllib.error.HTTPError as e:
            print(f"❌ {endpoint}: {e.status} - {e.reason}")
        except Exception as e:
            print(f"💥 {endpoint}: ERROR - {e}")

def test_server_headers():
    """Check server headers to identify what's running."""
    print("\nCHECKING SERVER HEADERS")
    print("=" * 30)
    
    try:
        req = urllib.request.Request("http://localhost:8000/health")
        with urllib.request.urlopen(req) as response:
            print("Response Headers:")
            for header, value in response.headers.items():
                print(f"  {header}: {value}")
                
            print(f"\nStatus: {response.status}")
            print(f"Response: {response.read().decode()}")
            
    except Exception as e:
        print(f"Header check error: {e}")

def test_with_custom_headers():
    """Test with custom headers to see if they affect response."""
    print("\nTESTING WITH CUSTOM HEADERS")
    print("=" * 30)
    
    test_headers = {
        'User-Agent': 'DebugTest/1.0',
        'X-Debug': 'true',
        'X-Test': 'middleware-test'
    }
    
    try:
        # Test health endpoint
        req = urllib.request.Request(
            "http://localhost:8000/health",
            headers=test_headers
        )
        
        with urllib.request.urlopen(req) as response:
            print(f"Health with custom headers: {response.status}")
            
        # Test login endpoint
        data = urllib.parse.urlencode({'username': 'test', 'password': 'test'}).encode()
        test_headers['Content-Type'] = 'application/x-www-form-urlencoded'
        
        req = urllib.request.Request(
            "http://localhost:8000/api/v1/auth/login",
            data=data,
            headers=test_headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req) as response:
            print(f"Login with custom headers: {response.status}")
            
    except urllib.error.HTTPError as e:
        print(f"Custom headers test: {e.status} - {e.reason}")
    except Exception as e:
        print(f"Custom headers error: {e}")

if __name__ == "__main__":
    check_port_8000()
    test_different_endpoints()
    test_server_headers()
    test_with_custom_headers()