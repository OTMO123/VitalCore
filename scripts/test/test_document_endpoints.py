#!/usr/bin/env python3
"""
Test document management endpoints for React frontend components
Tests 5 main frontend integrations:
1. Drag-drop file uploads
2. Document viewer with preview capabilities  
3. Patient document history interface
4. Search and filtering functionality
5. Bulk operations interface
"""

import requests
import json
import os
from typing import Dict, Any

class DocumentEndpointTester:
    def __init__(self):
        self.base_url = "http://localhost:8003"
        self.token = None
        self.headers = {"Content-Type": "application/json"}
        
    def authenticate(self) -> bool:
        """Authenticate and get access token"""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                data={"username": "admin", "password": "admin123"},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.headers["Authorization"] = f"Bearer {self.token}"
                print("OK Authentication successful")
                return True
            else:
                print(f"ERROR Authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"ERROR Authentication error: {e}")
            return False
    
    def test_endpoint(self, method: str, endpoint: str, data: Dict[Any, Any] = None, files: Dict[str, Any] = None) -> Dict[str, Any]:
        """Test an endpoint and return results"""
        try:
            url = f"{self.base_url}{endpoint}"
            headers = self.headers.copy()
            
            if files:
                # Remove Content-Type for file uploads (requests sets it automatically)
                headers.pop("Content-Type", None)
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=data)
            elif method.upper() == "POST":
                if files:
                    response = requests.post(url, headers=headers, data=data, files=files)
                else:
                    response = requests.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                return {"status": "error", "message": "Unsupported method"}
            
            return {
                "status_code": response.status_code,
                "success": 200 <= response.status_code < 300,
                "response": response.text,
                "endpoint": endpoint,
                "method": method
            }
            
        except Exception as e:
            return {
                "status_code": 0,
                "success": False,
                "response": str(e),
                "endpoint": endpoint,
                "method": method
            }
    
    def print_result(self, test_name: str, result: Dict[str, Any]):
        """Print test result in a formatted way"""
        status = "OK" if result["success"] else "ERROR"
        print(f"{status} {test_name}")
        print(f"  Endpoint: {result['method']} {result['endpoint']}")
        print(f"  Status: {result['status_code']}")
        
        if not result["success"]:
            print(f"  Error: {result['response']}")
        else:
            try:
                # Try to parse JSON response
                response_data = json.loads(result["response"])
                if isinstance(response_data, dict):
                    print(f"  Response keys: {list(response_data.keys())}")
                elif isinstance(response_data, list):
                    print(f"  Response items: {len(response_data)}")
            except:
                print(f"  Response length: {len(result['response'])}")
        print()
    
    def test_document_management_endpoints(self):
        """Test all document management endpoints for frontend integration"""
        
        print("=" * 60)
        print("DOCUMENT MANAGEMENT ENDPOINTS TEST")
        print("Testing endpoints for 5 React components")
        print("=" * 60)
        
        if not self.authenticate():
            print("Cannot proceed without authentication")
            return
        
        print("\n1. DRAG-DROP FILE UPLOAD COMPONENT")
        print("-" * 40)
        
        # Test file upload endpoint
        result = self.test_endpoint("POST", "/api/v1/documents/upload")
        self.print_result("File Upload Endpoint", result)
        
        # Test upload status check
        result = self.test_endpoint("GET", "/api/v1/documents/upload/status/test-id")
        self.print_result("Upload Status Check", result)
        
        # Test supported file types
        result = self.test_endpoint("GET", "/api/v1/documents/supported-types")
        self.print_result("Supported File Types", result)
        
        print("\n2. DOCUMENT VIEWER WITH PREVIEW")
        print("-" * 40)
        
        # Test document list
        result = self.test_endpoint("GET", "/api/v1/documents")
        self.print_result("Document List", result)
        
        # Test document metadata
        result = self.test_endpoint("GET", "/api/v1/documents/test-doc-id")
        self.print_result("Document Metadata", result)
        
        # Test document preview
        result = self.test_endpoint("GET", "/api/v1/documents/test-doc-id/preview")
        self.print_result("Document Preview", result)
        
        # Test document download
        result = self.test_endpoint("GET", "/api/v1/documents/test-doc-id/download")
        self.print_result("Document Download", result)
        
        print("\n3. PATIENT DOCUMENT HISTORY")
        print("-" * 40)
        
        # Test patient documents
        result = self.test_endpoint("GET", "/api/v1/patients/test-patient-id/documents")
        self.print_result("Patient Documents", result)
        
        # Test document history/versions
        result = self.test_endpoint("GET", "/api/v1/documents/test-doc-id/history")
        self.print_result("Document History", result)
        
        # Test patient document timeline
        result = self.test_endpoint("GET", "/api/v1/patients/test-patient-id/timeline")
        self.print_result("Patient Document Timeline", result)
        
        print("\n4. SEARCH AND FILTERING")
        print("-" * 40)
        
        # Test document search
        search_params = {
            "query": "test",
            "type": "pdf",
            "patient_id": "test-patient-id",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31"
        }
        result = self.test_endpoint("GET", "/api/v1/documents/search", data=search_params)
        self.print_result("Document Search", result)
        
        # Test advanced search
        result = self.test_endpoint("POST", "/api/v1/documents/search/advanced", data={
            "filters": {
                "document_type": ["pdf", "image"],
                "classification": ["phi"],
                "size_range": {"min": 0, "max": 10485760}
            }
        })
        self.print_result("Advanced Search", result)
        
        # Test search suggestions
        result = self.test_endpoint("GET", "/api/v1/documents/search/suggestions", data={"q": "test"})
        self.print_result("Search Suggestions", result)
        
        print("\n5. BULK OPERATIONS")
        print("-" * 40)
        
        # Test bulk document operations
        bulk_data = {
            "document_ids": ["doc1", "doc2", "doc3"],
            "operation": "move",
            "target_location": "/new/folder"
        }
        result = self.test_endpoint("POST", "/api/v1/documents/bulk", data=bulk_data)
        self.print_result("Bulk Operations", result)
        
        # Test bulk classification
        classification_data = {
            "document_ids": ["doc1", "doc2"],
            "classification": "phi"
        }
        result = self.test_endpoint("POST", "/api/v1/documents/bulk/classify", data=classification_data)
        self.print_result("Bulk Classification", result)
        
        # Test bulk export
        export_data = {
            "document_ids": ["doc1", "doc2"],
            "format": "zip",
            "include_metadata": True
        }
        result = self.test_endpoint("POST", "/api/v1/documents/bulk/export", data=export_data)
        self.print_result("Bulk Export", result)
        
        print("\n6. ADDITIONAL FRONTEND ENDPOINTS")
        print("-" * 40)
        
        # Test document statistics for dashboard
        result = self.test_endpoint("GET", "/api/v1/documents/stats")
        self.print_result("Document Statistics", result)
        
        # Test recent documents
        result = self.test_endpoint("GET", "/api/v1/documents/recent")
        self.print_result("Recent Documents", result)
        
        # Test document sharing
        share_data = {
            "document_id": "test-doc-id",
            "shared_with": ["user1@example.com"],
            "permissions": ["read"],
            "expires_at": "2025-12-31T23:59:59Z"
        }
        result = self.test_endpoint("POST", "/api/v1/documents/share", data=share_data)
        self.print_result("Document Sharing", result)
        
        print("\n" + "=" * 60)
        print("DOCUMENT ENDPOINT TESTING COMPLETED")
        print("=" * 60)
        
        print("\nNEXT STEPS:")
        print("1. Implement missing endpoints that returned 404")
        print("2. Update React components to use working endpoints")
        print("3. Add proper error handling for failed endpoints")
        print("4. Test with real file uploads and data")

def main():
    tester = DocumentEndpointTester()
    tester.test_document_management_endpoints()

if __name__ == "__main__":
    main()