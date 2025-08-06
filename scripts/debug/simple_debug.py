#!/usr/bin/env python3

import urllib.request
import urllib.parse

def simple_test():
    print("SIMPLE SERVER TEST")
    print("=" * 30)
    
    # Test health
    try:
        with urllib.request.urlopen("http://localhost:8000/health") as response:
            headers = dict(response.headers)
            print(f"Health: {response.status}")
            print(f"Server header: {headers.get('server', 'unknown')}")
            print(f"Date header: {headers.get('date', 'unknown')}")
    except Exception as e:
        print(f"Health error: {e}")
    
    # Test login
    try:
        data = urllib.parse.urlencode({'username': 'admin', 'password': 'admin123'}).encode()
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        req = urllib.request.Request("http://localhost:8000/api/v1/auth/login", data=data, headers=headers, method='POST')
        
        with urllib.request.urlopen(req) as response:
            print(f"Login: {response.status}")
    except urllib.error.HTTPError as e:
        error_data = e.read().decode()
        response_headers = dict(e.headers)
        print(f"Login: {e.status}")
        print(f"Error: {error_data}")
        print(f"Server header: {response_headers.get('server', 'unknown')}")
    except Exception as e:
        print(f"Login error: {e}")

if __name__ == "__main__":
    simple_test()