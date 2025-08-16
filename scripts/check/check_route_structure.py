#!/usr/bin/env python3
"""
Check route structure in clinical workflows
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the router directly
from app.modules.clinical_workflows.router import router

def check_routes():
    print("Clinical Workflows Router Analysis")
    print("=" * 40)
    
    # Get all routes from the router
    routes = router.routes
    
    print(f"Total routes: {len(routes)}")
    
    for route in routes:
        if hasattr(route, 'path'):
            print(f"Route: {route.path}")
            if hasattr(route, 'methods'):
                print(f"  Methods: {route.methods}")
        print()
    
    # Check router prefix
    print(f"Router prefix: {getattr(router, 'prefix', 'None')}")
    print(f"Router tags: {getattr(router, 'tags', 'None')}")

if __name__ == "__main__":
    check_routes()