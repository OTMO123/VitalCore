#!/usr/bin/env python3
"""
Debug script to check import issues in performance tests
"""

try:
    # Test all imports from the failing test
    print("Testing imports...")
    
    # Core imports
    from app.core.load_testing import (
        LoadTestStrategy, PerformanceMetricType, LoadTestConfig,
        LoadTestOrchestrator, PerformanceRegressionDetector, PerformanceMonitor
    )
    print("✅ Core load_testing imports successful")
    
    from app.core.database_performance import (
        DatabasePerformanceMonitor, OptimizedConnectionPool, 
        QueryPerformanceStats, ConnectionPoolStats
    )
    print("✅ Database performance imports successful")
    
    # Healthcare modules
    from app.core.database_unified import get_db
    from app.modules.audit_logger.schemas import AuditEvent as AuditLog
    from app.core.database_unified import User
    print("✅ Database unified imports successful")
    
    from app.modules.healthcare_records.models import Patient, Immunization
    print("✅ Healthcare records models imports successful")
    
    from app.modules.healthcare_records.fhir_r4_resources import (
        FHIRResourceType, FHIRResourceFactory
    )
    print("✅ FHIR R4 resources imports successful")
    
    from app.modules.healthcare_records.fhir_rest_api import (
        FHIRRestService, FHIRBundle, BundleType
    )
    print("✅ FHIR REST API imports successful")
    
    from app.modules.iris_api.client import IRISAPIClient
    from app.modules.iris_api.service import IRISIntegrationService
    print("✅ IRIS API imports successful")
    
    from app.core.security import security_manager
    print("✅ Security imports successful")
    
    print("\n🎉 ALL IMPORTS SUCCESSFUL!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print(f"Failed import: {e.name if hasattr(e, 'name') else 'unknown'}")
    
    # Try to identify which specific import failed
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()

except Exception as e:
    print(f"❌ Other error: {e}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()