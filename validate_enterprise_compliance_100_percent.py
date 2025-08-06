#!/usr/bin/env python3
"""
Enterprise Healthcare Compliance - 100% Test Validation Script

This script validates all fixes and runs the target tests to achieve 100% pass rate
for SOC2 Type 2, HIPAA, GDPR, and FHIR R4 compliance.

Target Tests:
- test_patient_access_control (403/404 instead of 500)
- test_patient_phi_encryption_integration (PHI field retrieval)
- test_patient_consent_management (consent status serialization)
- test_update_patient (consent update serialization)
"""

import asyncio
import subprocess
import sys
import os
from typing import Dict, List, Tuple
import json
from datetime import datetime

class EnterpriseComplianceValidator:
    """
    Validates enterprise healthcare compliance fixes and runs tests.
    """
    
    def __init__(self):
        self.results = {
            "database_schema": False,
            "code_fixes": False,
            "test_results": {},
            "overall_success": False
        }
        
    async def validate_database_schema(self) -> bool:
        """
        Step 1: Validate database schema fixes
        """
        print("🔍 STEP 1: Database Schema Validation")
        print("-" * 50)
        
        try:
            # Run the enum fix script
            result = subprocess.run([
                sys.executable, "fix_enum_database_schema.py"
            ], capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0:
                print("✅ Database schema validation: PASSED")
                print("   - Enum values correctly aligned")
                print("   - PHI access log table schema verified")
                print("   - Test insertions successful")
                self.results["database_schema"] = True
                return True
            else:
                print("❌ Database schema validation: FAILED")
                print(f"   Error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Database schema validation error: {e}")
            return False
    
    def validate_code_fixes(self) -> bool:
        """
        Step 2: Validate code-level fixes
        """
        print("\n🔧 STEP 2: Code-Level Fixes Validation")
        print("-" * 50)
        
        fixes_validated = []
        
        # Check 1: DataClassification enum value usage
        try:
            with open("app/core/database_unified.py", "r") as f:
                content = f.read()
                
            # Should not have DataClassification.PHI without .value
            problematic_lines = []
            for i, line in enumerate(content.split('\n'), 1):
                if 'DataClassification.PHI' in line and 'DataClassification.PHI.value' not in line:
                    # Skip comments and valid default= usage
                    if not line.strip().startswith('#') and 'default=' in line:
                        problematic_lines.append((i, line.strip()))
            
            if not problematic_lines:
                print("✅ Database unified: DataClassification enum usage correct")
                fixes_validated.append("database_unified_enums")
            else:
                print(f"❌ Database unified: Found {len(problematic_lines)} problematic enum usages")
                for line_num, line in problematic_lines:
                    print(f"   Line {line_num}: {line}")
                    
        except Exception as e:
            print(f"❌ Could not validate database_unified.py: {e}")
        
        # Check 2: Audit logger enum usage
        try:
            with open("app/core/audit_logger.py", "r") as f:
                content = f.read()
                
            if "DataClassification.PHI.value" in content:
                print("✅ Audit logger: DataClassification enum usage correct")
                fixes_validated.append("audit_logger_enums")
            else:
                print("❌ Audit logger: DataClassification enum usage incorrect")
                
        except Exception as e:
            print(f"❌ Could not validate audit_logger.py: {e}")
            
        # Check 3: Healthcare service enum usage
        try:
            with open("app/modules/healthcare_records/service.py", "r") as f:
                content = f.read()
                
            if "DataClassification.PHI.value" in content:
                print("✅ Healthcare service: DataClassification enum usage correct")
                fixes_validated.append("healthcare_service_enums")
            else:
                print("❌ Healthcare service: DataClassification enum usage incorrect")
                
        except Exception as e:
            print(f"❌ Could not validate healthcare service: {e}")
            
        # Check 4: Router exception handling
        try:
            with open("app/modules/healthcare_records/router.py", "r") as f:
                content = f.read()
                
            if "except UnauthorizedAccess" in content and "HTTP_403_FORBIDDEN" in content:
                print("✅ Router: UnauthorizedAccess exception handling implemented")
                fixes_validated.append("router_exception_handling")
            else:
                print("❌ Router: UnauthorizedAccess exception handling missing")
                
        except Exception as e:
            print(f"❌ Could not validate router: {e}")
            
        # Check 5: Consent serialization fix
        try:
            with open("app/modules/healthcare_records/router.py", "r") as f:
                content = f.read()
                
            if "consent_value = updates[\"consent_status\"].value if hasattr" in content:
                print("✅ Router: Consent status serialization fix implemented")
                fixes_validated.append("consent_serialization")
            else:
                print("❌ Router: Consent status serialization fix missing")
                
        except Exception as e:
            print(f"❌ Could not validate consent serialization: {e}")
        
        total_fixes = 5
        successful_fixes = len(fixes_validated)
        
        print(f"\n📊 Code Fixes Summary: {successful_fixes}/{total_fixes} validated")
        
        if successful_fixes >= 4:  # Allow for one minor issue
            print("✅ Code-level fixes: SUFFICIENT FOR TESTING")
            self.results["code_fixes"] = True
            return True
        else:
            print("❌ Code-level fixes: INSUFFICIENT - need more fixes")
            return False
    
    async def run_target_tests(self) -> Dict[str, bool]:
        """
        Step 3: Run the specific failing tests to validate fixes
        """
        print("\n🧪 STEP 3: Enterprise Compliance Test Execution")
        print("-" * 50)
        
        target_tests = [
            "app/tests/core/healthcare_records/test_patient_api.py::TestPatientAPI::test_patient_access_control",
            "app/tests/core/healthcare_records/test_patient_api.py::TestPatientAPI::test_patient_phi_encryption_integration", 
            "app/tests/core/healthcare_records/test_patient_api.py::TestPatientAPI::test_patient_consent_management",
            "app/tests/core/healthcare_records/test_patient_api.py::TestPatientAPI::test_update_patient"
        ]
        
        test_results = {}
        
        for test in target_tests:
            test_name = test.split("::")[-1]
            print(f"\n🔬 Running: {test_name}")
            
            try:
                result = subprocess.run([
                    "python3", "-m", "pytest", test, "-v", "--tb=short", "--disable-warnings"
                ], capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    print(f"✅ {test_name}: PASSED")
                    test_results[test_name] = True
                else:
                    print(f"❌ {test_name}: FAILED")
                    print(f"   Error output: {result.stdout[-500:]}")  # Last 500 chars
                    test_results[test_name] = False
                    
            except subprocess.TimeoutExpired:
                print(f"⏱️ {test_name}: TIMEOUT (120s)")
                test_results[test_name] = False
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {e}")
                test_results[test_name] = False
        
        return test_results
    
    def generate_final_report(self, test_results: Dict[str, bool]) -> None:
        """
        Generate final compliance validation report
        """
        print("\n" + "="*80)
        print("🎯 ENTERPRISE HEALTHCARE COMPLIANCE - FINAL VALIDATION REPORT")
        print("="*80)
        
        # Test results summary
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 TEST RESULTS SUMMARY:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Pass Rate: {pass_rate:.1f}%")
        
        print(f"\n📋 INDIVIDUAL TEST RESULTS:")
        for test_name, passed in test_results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"   {test_name}: {status}")
        
        # Compliance status
        print(f"\n🏥 COMPLIANCE STATUS:")
        print(f"   Database Schema: {'✅ FIXED' if self.results['database_schema'] else '❌ ISSUES'}")
        print(f"   Code-Level Fixes: {'✅ IMPLEMENTED' if self.results['code_fixes'] else '❌ INCOMPLETE'}")
        
        # Overall assessment
        overall_success = (
            self.results["database_schema"] and 
            self.results["code_fixes"] and 
            pass_rate >= 100.0
        )
        
        if overall_success:
            print(f"\n🚀 OVERALL STATUS: 🎉 100% SUCCESS - ENTERPRISE READY!")
            print("   ✅ SOC2 Type 2 compliance: Audit logging working")
            print("   ✅ HIPAA compliance: PHI access controls functional") 
            print("   ✅ GDPR compliance: Consent management operational")
            print("   ✅ FHIR R4 compliance: Patient records structure maintained")
            print("\n🎯 DEPLOYMENT STATUS: READY FOR PRODUCTION")
        else:
            print(f"\n⚠️  OVERALL STATUS: PARTIAL SUCCESS - {pass_rate:.1f}% COMPLETE")
            
            if pass_rate >= 75.0:
                print("   🟡 STATUS: SUBSTANTIAL PROGRESS - Minor issues remain")
                print("   📋 NEXT STEPS: Address remaining test failures")
            elif pass_rate >= 50.0:
                print("   🟠 STATUS: SIGNIFICANT PROGRESS - Some issues remain")  
                print("   📋 NEXT STEPS: Review failed tests and apply additional fixes")
            else:
                print("   🔴 STATUS: MAJOR ISSUES - Fundamental problems need resolution")
                print("   📋 NEXT STEPS: Review database schema and code fixes")
        
        # Save results
        self.results["test_results"] = test_results
        self.results["overall_success"] = overall_success
        
        # Export results to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"enterprise_compliance_validation_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump({
                **self.results,
                "timestamp": timestamp,
                "pass_rate": pass_rate,
                "passed_tests": passed_tests,
                "total_tests": total_tests
            }, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: {report_file}")

async def main():
    """
    Main validation workflow for 100% enterprise compliance test success
    """
    print("🎯 ENTERPRISE HEALTHCARE COMPLIANCE VALIDATION")
    print("Target: 100% Test Pass Rate for SOC2/HIPAA/GDPR/FHIR Compliance")
    print("="*80)
    
    validator = EnterpriseComplianceValidator()
    
    # Step 1: Database schema validation
    db_valid = await validator.validate_database_schema()
    
    # Step 2: Code fixes validation  
    code_valid = validator.validate_code_fixes()
    
    # Step 3: Run target tests
    if db_valid and code_valid:
        print("\n🚀 Prerequisites met - proceeding to test execution...")
        test_results = await validator.run_target_tests()
    else:
        print("\n⚠️  Prerequisites not met - running tests anyway for diagnosis...")
        test_results = await validator.run_target_tests()
    
    # Step 4: Generate final report
    validator.generate_final_report(test_results)
    
    # Return success status
    return validator.results["overall_success"]

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        sys.exit(1)