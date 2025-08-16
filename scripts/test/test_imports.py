#!/usr/bin/env python3
"""
Test script to verify all imports in compliance test files work correctly.
"""

import sys
import traceback

def test_imports():
    """Test all critical imports for compliance tests."""
    
    print("Testing imports for compliance test files...")
    
    # Test 1: Core database imports
    try:
        from app.core.database_unified import get_db, User, Patient, Role
        print("✓ Core database imports: SUCCESS")
    except Exception as e:
        print(f"✗ Core database imports: FAILED - {e}")
        traceback.print_exc()
        return False
    
    # Test 2: FHIR R4 schemas
    try:
        from app.schemas.fhir_r4 import FHIRPatient, FHIRImmunization
        print("✓ FHIR R4 schemas: SUCCESS") 
    except Exception as e:
        print(f"✗ FHIR R4 schemas: FAILED - {e}")
        traceback.print_exc()
        return False
    
    # Test 3: Healthcare records models
    try:
        from app.modules.healthcare_records.models import Immunization
        print("✓ Healthcare records models: SUCCESS")
    except Exception as e:
        print(f"✗ Healthcare records models: FAILED - {e}")
        traceback.print_exc()
        return False
    
    # Test 4: FHIR R4 resources
    try:
        from app.modules.healthcare_records.fhir_r4_resources import (
            FHIRResourceType, FHIRResourceFactory,
            FHIRAppointment, FHIRCarePlan, FHIRProcedure, BaseFHIRResource,
            AppointmentStatus, CarePlanStatus, ProcedureStatus,
            Identifier, CodeableConcept, Reference, Period, Annotation
        )
        print("✓ FHIR R4 resources: SUCCESS")
    except Exception as e:
        print(f"✗ FHIR R4 resources: FAILED - {e}")
        traceback.print_exc()
        return False
    
    # Test 5: FHIR REST API
    try:
        from app.modules.healthcare_records.fhir_rest_api import (
            FHIRRestService, FHIRBundle, FHIRSearchParams, BundleType,
            HTTPVerb, BundleEntry, BundleEntryRequest, BundleEntryResponse
        )
        print("✓ FHIR REST API: SUCCESS")
    except Exception as e:
        print(f"✗ FHIR REST API: FAILED - {e}")
        traceback.print_exc()
        return False
    
    # Test 6: FHIR validator
    try:
        from app.modules.healthcare_records.fhir_validator import FHIRValidator
        print("✓ FHIR validator: SUCCESS")
    except Exception as e:
        print(f"✗ FHIR validator: FAILED - {e}")
        traceback.print_exc()
        return False
    
    # Test 7: Audit logger schemas
    try:
        from app.modules.audit_logger.schemas import AuditEvent as AuditLog
        print("✓ Audit logger schemas: SUCCESS")
    except Exception as e:
        print(f"✗ Audit logger schemas: FAILED - {e}")
        traceback.print_exc()
        return False
    
    # Test 8: Security and config
    try:
        from app.core.security import SecurityManager, encryption_service
        from app.core.config import get_settings
        print("✓ Security and config: SUCCESS")
    except Exception as e:
        print(f"✗ Security and config: FAILED - {e}")
        traceback.print_exc()
        return False
    
    print("\n🎉 All imports successful! Compliance tests should now be able to collect without import errors.")
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)