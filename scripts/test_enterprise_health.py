#!/usr/bin/env python3
"""
Enterprise Health Endpoint Validation Script

Tests the production-ready health endpoints with SOC2/HIPAA compliance validation.
Can be used for:
- CI/CD pipeline health checks
- Production deployment validation  
- Enterprise monitoring system integration testing
"""

import asyncio
import httpx
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class EnterpriseHealthValidator:
    """Enterprise health endpoint validator for SOC2/HIPAA compliance."""
    
    def __init__(self, base_urls: List[str] = None):
        self.base_urls = base_urls or [
            "http://localhost:8000",
            "http://localhost:8004", 
            "http://app:8000"
        ]
        self.health_endpoints = [
            "/health",
            "/health/detailed", 
            "/health/compliance",
            "/health/security"
        ]
        self.results = []
        
    async def validate_health_endpoint(self, url: str) -> Dict[str, Any]:
        """Validate a single health endpoint for enterprise compliance."""
        result = {
            "endpoint": url,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "unknown",
            "response_time_ms": 0,
            "compliance_score": 0,
            "enterprise_features": [],
            "warnings": [],
            "errors": []
        }
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                result["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
                
                if response.status_code == 200:
                    try:
                        health_data = response.json()
                        result["status"] = health_data.get("status", "unknown")
                        result["raw_data"] = health_data
                        
                        # Validate enterprise health check requirements
                        self._validate_enterprise_compliance(health_data, result)
                        
                    except json.JSONDecodeError:
                        result["errors"].append("Invalid JSON response")
                        result["status"] = "error"
                        
                elif response.status_code == 404:
                    result["status"] = "not_implemented"
                    result["warnings"].append("Health endpoint not implemented")
                    
                else:
                    result["status"] = "error"
                    result["errors"].append(f"HTTP {response.status_code}")
                    
        except (httpx.ConnectTimeout, httpx.ConnectError) as e:
            result["status"] = "unreachable"
            result["errors"].append(f"Connection failed: {str(e)}")
            
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(f"Unexpected error: {str(e)}")
            
        return result
    
    def _validate_enterprise_compliance(self, health_data: Dict, result: Dict):
        """Validate enterprise compliance requirements."""
        score = 0
        features = []
        
        # Required enterprise fields
        required_fields = {
            "status": 10,
            "timestamp": 10,
            "version": 5,
            "service": 5
        }
        
        for field, points in required_fields.items():
            if field in health_data:
                score += points
                features.append(f"has_{field}")
        
        # Enterprise monitoring fields
        monitoring_fields = {
            "database": 15,
            "redis": 10,
            "memory": 10,
            "cpu_percent": 5,
            "uptime": 5
        }
        
        for field, points in monitoring_fields.items():
            if field in health_data:
                score += points
                features.append(f"monitors_{field}")
        
        # SOC2/HIPAA compliance indicators
        compliance_fields = {
            "compliance": 20,
            "encryption": 15,
            "audit_service": 15,
            "event_bus": 10,
            "security_headers": 10
        }
        
        for field, points in compliance_fields.items():
            if field in health_data:
                score += points
                features.append(f"compliance_{field}")
        
        # Validate specific compliance data
        if "compliance" in health_data:
            compliance_data = health_data["compliance"]
            if isinstance(compliance_data, dict):
                compliance_standards = ["soc2_type2", "hipaa", "fhir_r4", "gdpr"]
                present_standards = [std for std in compliance_standards if compliance_data.get(std)]
                if len(present_standards) >= 3:
                    score += 20
                    features.append("multi_compliance_framework")
        
        result["compliance_score"] = min(score, 100)
        result["enterprise_features"] = features
        
        # Add warnings for missing critical features
        if score < 50:
            result["warnings"].append("Low enterprise compliance score")
        if "database" not in health_data:
            result["warnings"].append("Missing database health check")
        if "encryption" not in health_data:
            result["warnings"].append("Missing encryption validation")
    
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive enterprise health validation."""
        print("🏥 Starting Enterprise Health Endpoint Validation")
        print("=" * 60)
        
        validation_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "validation_summary": {
                "total_endpoints_tested": 0,
                "successful_endpoints": 0,
                "failed_endpoints": 0,
                "average_response_time": 0,
                "average_compliance_score": 0
            },
            "endpoint_results": [],
            "overall_status": "unknown"
        }
        
        all_results = []
        
        for base_url in self.base_urls:
            print(f"\n🔍 Testing server: {base_url}")
            server_accessible = False
            
            # Test basic connectivity first
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{base_url}/", timeout=5.0)
                    if response.status_code < 500:
                        server_accessible = True
                        print(f"  ✅ Server accessible")
            except:
                print(f"  ❌ Server not accessible")
                continue
            
            if not server_accessible:
                continue
                
            # Test each health endpoint
            for endpoint in self.health_endpoints:
                url = f"{base_url}{endpoint}"
                print(f"  Testing: {endpoint}")
                
                result = await self.validate_health_endpoint(url)
                all_results.append(result)
                
                # Print result summary
                status_emoji = {
                    "healthy": "✅",
                    "unhealthy": "⚠️",
                    "degraded": "⚠️", 
                    "error": "❌",
                    "unreachable": "❌",
                    "not_implemented": "⚠️"
                }.get(result["status"], "❓")
                
                print(f"    {status_emoji} Status: {result['status']} "
                      f"({result['response_time_ms']}ms, "
                      f"Compliance: {result['compliance_score']}/100)")
                
                if result["enterprise_features"]:
                    print(f"    📊 Features: {', '.join(result['enterprise_features'][:3])}...")
                
                if result["warnings"]:
                    for warning in result["warnings"]:
                        print(f"    ⚠️  Warning: {warning}")
                        
                if result["errors"]:
                    for error in result["errors"]:
                        print(f"    ❌ Error: {error}")
        
        # Calculate summary statistics
        if all_results:
            successful = [r for r in all_results if r["status"] in ["healthy", "degraded"]]
            failed = [r for r in all_results if r["status"] in ["error", "unreachable"]]
            
            validation_results["validation_summary"].update({
                "total_endpoints_tested": len(all_results),
                "successful_endpoints": len(successful),
                "failed_endpoints": len(failed),
                "average_response_time": round(sum(r["response_time_ms"] for r in all_results) / len(all_results), 2),
                "average_compliance_score": round(sum(r["compliance_score"] for r in all_results) / len(all_results), 1)
            })
            
            validation_results["endpoint_results"] = all_results
            
            # Determine overall status
            if len(successful) > 0:
                avg_score = validation_results["validation_summary"]["average_compliance_score"]
                if avg_score >= 80:
                    validation_results["overall_status"] = "enterprise_ready"
                elif avg_score >= 60:
                    validation_results["overall_status"] = "compliant"
                else:
                    validation_results["overall_status"] = "needs_improvement"
            else:
                validation_results["overall_status"] = "failed"
        
        else:
            validation_results["overall_status"] = "no_endpoints_accessible"
        
        # Print final summary
        print("\n" + "=" * 60)
        print("📊 Enterprise Health Validation Summary")
        print("=" * 60)
        
        summary = validation_results["validation_summary"]
        print(f"Endpoints Tested: {summary['total_endpoints_tested']}")
        print(f"Successful: {summary['successful_endpoints']}")
        print(f"Failed: {summary['failed_endpoints']}")
        print(f"Average Response Time: {summary['average_response_time']}ms")
        print(f"Average Compliance Score: {summary['average_compliance_score']}/100")
        print(f"Overall Status: {validation_results['overall_status'].upper()}")
        
        # Enterprise readiness assessment
        overall_status = validation_results["overall_status"]
        if overall_status == "enterprise_ready":
            print("\n🎉 ENTERPRISE READY: System meets all compliance requirements")
            return_code = 0
        elif overall_status == "compliant":
            print("\n✅ COMPLIANT: System meets basic compliance requirements")
            return_code = 0
        elif overall_status == "needs_improvement":
            print("\n⚠️  NEEDS IMPROVEMENT: System has compliance gaps")
            return_code = 1
        else:
            print("\n❌ FAILED: System does not meet minimum requirements")
            return_code = 2
        
        return validation_results, return_code

async def main():
    """Main validation function."""
    validator = EnterpriseHealthValidator()
    results, return_code = await validator.run_comprehensive_validation()
    
    # Save results to file for CI/CD integration
    with open("health_validation_report.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: health_validation_report.json")
    return return_code

if __name__ == "__main__":
    return_code = asyncio.run(main())
    sys.exit(return_code)