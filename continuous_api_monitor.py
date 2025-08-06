#!/usr/bin/env python3
"""
Continuous API Endpoint Monitor
Real-time monitoring of all API endpoints to ensure 100% functionality
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

@dataclass
class EndpointTest:
    method: str
    path: str
    name: str
    requires_auth: bool = True
    expected_status: int = 200
    test_data: Optional[Dict] = None
    headers: Optional[Dict] = None
    description: str = ""

@dataclass
class TestResult:
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    success: bool
    error: Optional[str] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

class ContinuousAPIMonitor:
    """Continuously monitors all API endpoints for functionality"""
    
    def __init__(self, base_url: str = "http://localhost:8000", 
                 check_interval: int = 30):
        self.base_url = base_url.rstrip('/')
        self.check_interval = check_interval
        self.session: Optional[aiohttp.ClientSession] = None
        self.auth_token: Optional[str] = None
        self.results: List[TestResult] = []
        self.setup_logging()
        
        # Define all API endpoints to monitor
        self.endpoints = [
            # Health endpoints
            EndpointTest("GET", "/health", "Basic Health Check", False, 200, 
                        description="Basic system health"),
            EndpointTest("GET", "/health/detailed", "Detailed Health Check", False, 200,
                        description="Detailed system health"),
            
            # Authentication endpoints
            EndpointTest("POST", "/api/v1/auth/login", "User Login", False, 200,
                        test_data={"username": "admin", "password": "admin123"},
                        description="User authentication"),
            EndpointTest("GET", "/api/v1/auth/me", "Get Current User", True, 200,
                        description="Get current user info"),
            EndpointTest("POST", "/api/v1/auth/refresh", "Refresh Token", True, 200,
                        description="Token refresh"),
            
            # Patient management endpoints
            EndpointTest("GET", "/api/v1/patients", "List Patients", True, 200,
                        description="List all patients"),
            EndpointTest("POST", "/api/v1/patients", "Create Patient", True, 201,
                        test_data={
                            "first_name": "Test",
                            "last_name": "Patient",
                            "date_of_birth": "1990-01-01",
                            "gender": "male",
                            "email": "test@example.com"
                        },
                        description="Create new patient"),
            
            # Clinical workflows endpoints
            EndpointTest("GET", "/api/v1/clinical-workflows", "List Workflows", True, 200,
                        description="List clinical workflows"),
            EndpointTest("POST", "/api/v1/clinical-workflows", "Create Workflow", True, 201,
                        test_data={
                            "workflow_type": "routine_checkup",
                            "patient_id": "550e8400-e29b-41d4-a716-446655440000",
                            "priority": "medium",
                            "description": "Test workflow"
                        },
                        description="Create clinical workflow"),
            EndpointTest("GET", "/api/v1/clinical-workflows/health", "Workflow Health", False, 200,
                        description="Clinical workflow health"),
            
            # Audit logging endpoints
            EndpointTest("GET", "/api/v1/audit-logs", "List Audit Logs", True, 200,
                        description="List audit logs"),
            EndpointTest("GET", "/api/v1/audit-logs/security-events", "Security Events", True, 200,
                        description="List security events"),
            
            # IRIS API endpoints
            EndpointTest("GET", "/api/v1/iris", "IRIS Status", True, 200,
                        description="IRIS API status"),
            EndpointTest("GET", "/api/v1/iris/health", "IRIS Health", False, 200,
                        description="IRIS health check"),
            
            # Analytics endpoints
            EndpointTest("GET", "/api/v1/analytics/dashboard", "Analytics Dashboard", True, 200,
                        description="Analytics dashboard data"),
            
            # Document management endpoints
            EndpointTest("GET", "/api/v1/documents", "List Documents", True, 200,
                        description="List documents"),
            
            # Risk stratification endpoints
            EndpointTest("GET", "/api/v1/risk-stratification/health", "Risk Health", False, 200,
                        description="Risk stratification health"),
        ]
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('api_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def start_session(self):
        """Start aiohttp session"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def authenticate(self) -> bool:
        """Authenticate and get access token"""
        try:
            auth_data = {"username": "admin", "password": "admin123"}
            url = f"{self.base_url}/api/v1/auth/login"
            
            async with self.session.post(url, json=auth_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("access_token")
                    self.logger.info("✅ Authentication successful")
                    return True
                else:
                    self.logger.error(f"❌ Authentication failed: {response.status}")
                    return False
        except Exception as e:
            self.logger.error(f"❌ Authentication error: {e}")
            return False
    
    async def test_endpoint(self, endpoint: EndpointTest) -> TestResult:
        """Test a single endpoint"""
        start_time = time.time()
        url = f"{self.base_url}{endpoint.path}"
        
        # Prepare headers
        headers = endpoint.headers or {}
        if endpoint.requires_auth and self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        try:
            # Make the request
            if endpoint.method.upper() == "GET":
                async with self.session.get(url, headers=headers) as response:
                    status_code = response.status
                    response_time = (time.time() - start_time) * 1000
                    
            elif endpoint.method.upper() == "POST":
                async with self.session.post(url, json=endpoint.test_data, headers=headers) as response:
                    status_code = response.status
                    response_time = (time.time() - start_time) * 1000
                    
            elif endpoint.method.upper() == "PUT":
                async with self.session.put(url, json=endpoint.test_data, headers=headers) as response:
                    status_code = response.status
                    response_time = (time.time() - start_time) * 1000
                    
            elif endpoint.method.upper() == "DELETE":
                async with self.session.delete(url, headers=headers) as response:
                    status_code = response.status
                    response_time = (time.time() - start_time) * 1000
            
            # Check if test passed
            success = status_code == endpoint.expected_status
            error = None if success else f"Expected {endpoint.expected_status}, got {status_code}"
            
            return TestResult(
                endpoint=endpoint.path,
                method=endpoint.method,
                status_code=status_code,
                response_time_ms=round(response_time, 2),
                success=success,
                error=error
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return TestResult(
                endpoint=endpoint.path,
                method=endpoint.method,
                status_code=0,
                response_time_ms=round(response_time, 2),
                success=False,
                error=str(e)
            )
    
    async def run_all_tests(self) -> List[TestResult]:
        """Run all endpoint tests"""
        self.logger.info("🚀 Starting API endpoint tests...")
        
        # Authenticate first
        if not await self.authenticate():
            self.logger.error("❌ Failed to authenticate - skipping auth-required tests")
        
        results = []
        passed = 0
        failed = 0
        
        for endpoint in self.endpoints:
            # Skip auth-required tests if no token
            if endpoint.requires_auth and not self.auth_token:
                continue
                
            result = await self.test_endpoint(endpoint)
            results.append(result)
            
            if result.success:
                passed += 1
                self.logger.info(f"✅ {endpoint.method} {endpoint.path} - {result.response_time_ms}ms")
            else:
                failed += 1
                self.logger.error(f"❌ {endpoint.method} {endpoint.path} - {result.error}")
        
        # Log summary
        total = passed + failed
        success_rate = (passed / total * 100) if total > 0 else 0
        self.logger.info(f"📊 Results: {passed}/{total} passed ({success_rate:.1f}% success rate)")
        
        return results
    
    def save_results(self, results: List[TestResult]):
        """Save test results to file"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"api_test_results_{timestamp}.json"
        
        # Convert results to dictionaries
        results_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_tests": len(results),
            "passed": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success),
            "results": [asdict(r) for r in results]
        }
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        self.logger.info(f"💾 Results saved to {filename}")
    
    def generate_report(self, results: List[TestResult]) -> str:
        """Generate a formatted test report"""
        passed = sum(1 for r in results if r.success)
        failed = len(results) - passed
        success_rate = (passed / len(results) * 100) if results else 0
        
        report = f"""
🏥 HEALTHCARE API MONITORING REPORT
=====================================
📅 Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
📊 Total Tests: {len(results)}
✅ Passed: {passed}
❌ Failed: {failed}
📈 Success Rate: {success_rate:.1f}%

ENDPOINT DETAILS:
"""
        
        for result in results:
            status_icon = "✅" if result.success else "❌"
            report += f"{status_icon} {result.method} {result.endpoint} - {result.status_code} ({result.response_time_ms}ms)\n"
            if result.error:
                report += f"   Error: {result.error}\n"
        
        if failed > 0:
            report += f"\n⚠️  {failed} endpoints need attention!"
        else:
            report += f"\n🎉 All endpoints are working perfectly!"
        
        return report
    
    async def continuous_monitor(self):
        """Run continuous monitoring"""
        self.logger.info(f"🔄 Starting continuous API monitoring (interval: {self.check_interval}s)")
        
        while True:
            try:
                results = await self.run_all_tests()
                self.save_results(results)
                
                # Print report
                report = self.generate_report(results)
                print(report)
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                self.logger.info("⏹️  Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"❌ Monitor error: {e}")
                await asyncio.sleep(5)  # Short wait before retry
    
    async def single_run(self):
        """Run a single test cycle"""
        self.logger.info("🔄 Running single API test cycle...")
        results = await self.run_all_tests()
        self.save_results(results)
        
        # Print report
        report = self.generate_report(results)
        print(report)
        
        return results

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="API Endpoint Monitor")
    parser.add_argument("--base-url", default="http://localhost:8000", 
                       help="Base URL for API (default: http://localhost:8000)")
    parser.add_argument("--interval", type=int, default=30,
                       help="Check interval in seconds (default: 30)")
    parser.add_argument("--single", action="store_true",
                       help="Run single test cycle instead of continuous monitoring")
    
    args = parser.parse_args()
    
    monitor = ContinuousAPIMonitor(
        base_url=args.base_url,
        check_interval=args.interval
    )
    
    await monitor.start_session()
    
    try:
        if args.single:
            await monitor.single_run()
        else:
            await monitor.continuous_monitor()
    finally:
        await monitor.close_session()

if __name__ == "__main__":
    asyncio.run(main())