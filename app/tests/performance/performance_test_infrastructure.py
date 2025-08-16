"""
Enterprise Healthcare Performance Test Infrastructure

SOC2 Type 2, HIPAA, FHIR R4, GDPR Compliant Performance Testing Framework
Production-ready performance validation for healthcare systems.
"""

import asyncio
import time
import concurrent.futures
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timezone
import structlog
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
import psutil
import gc
import weakref

from app.core.database_unified import get_isolated_session_factory, HealthcareSessionManager
from app.core.performance_optimization import (
    PerformanceMonitor, HealthcareConnectionPool, HealthcareQueryOptimizer,
    FHIRPerformanceOptimizer, HealthcareLoadTester
)
from app.core.config import get_settings

logger = structlog.get_logger()

# ============================================
# HEALTHCARE PERFORMANCE TEST FRAMEWORK
# ============================================

@dataclass
class HealthcarePerformanceTestConfig:
    """Configuration for healthcare performance testing."""
    
    # Patient operation performance targets (SOC2 Type 2 requirements)
    patient_query_max_ms: int = 500
    immunization_query_max_ms: int = 300
    fhir_operation_max_ms: int = 3000
    phi_access_max_ms: int = 200
    
    # Throughput requirements (Enterprise scalability)
    min_requests_per_second: float = 100.0
    min_concurrent_users: int = 25
    max_memory_mb: float = 1000.0
    max_cpu_percent: float = 80.0
    max_error_rate_percent: float = 1.0
    
    # Database performance requirements
    max_connection_pool_size: int = 50
    max_query_timeout_ms: int = 30000
    max_transaction_time_ms: int = 10000
    
    # FHIR R4 specific requirements
    max_bundle_processing_ms: int = 3000
    max_resource_validation_ms: int = 500
    
    # Compliance monitoring
    audit_log_max_ms: int = 100
    encryption_max_ms: int = 50
    authentication_max_ms: int = 200

class HealthcarePerformanceTestFramework:
    """Enterprise healthcare performance testing framework."""
    
    def __init__(self, config: Optional[HealthcarePerformanceTestConfig] = None):
        self.config = config or HealthcarePerformanceTestConfig()
        self.performance_monitor = PerformanceMonitor()
        self.session_factory = None
        self.connection_pool = None
        self.query_optimizer = None
        self.fhir_optimizer = None
        self.test_results = {}
        self.initialized = False
    
    async def initialize(self):
        """Initialize performance test framework."""
        if self.initialized:
            return
        
        try:
            # Use isolated session factory for test isolation
            self.session_factory = await get_isolated_session_factory()
            self.connection_pool = HealthcareConnectionPool(self.session_factory)
            self.query_optimizer = HealthcareQueryOptimizer(self.connection_pool)
            self.fhir_optimizer = FHIRPerformanceOptimizer(self.connection_pool)
            
            self.initialized = True
            logger.info("Healthcare Performance Test Framework initialized")
            
        except Exception as e:
            logger.error("Failed to initialize performance test framework", error=str(e))
            raise
    
    async def cleanup(self):
        """Clean up test framework resources."""
        if self.connection_pool:
            await self.connection_pool.cleanup_stale_connections()
        
        # Force garbage collection
        gc.collect()
        
        logger.info("Performance test framework cleaned up")
    
    async def run_patient_registration_performance_test(
        self, 
        concurrent_users: int = 25,
        operations_per_user: int = 10
    ) -> Dict[str, Any]:
        """Run patient registration performance load test."""
        logger.info("Starting patient registration performance test",
                   concurrent_users=concurrent_users,
                   operations_per_user=operations_per_user)
        
        start_time = time.time()
        tasks = []
        
        # Create concurrent patient registration tasks
        for user_id in range(concurrent_users):
            task = asyncio.create_task(
                self._simulate_patient_registration_operations(user_id, operations_per_user)
            )
            tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Analyze results
        successful_operations = 0
        failed_operations = 0
        
        for result in results:
            if isinstance(result, Exception):
                failed_operations += operations_per_user
                logger.error("Patient registration task failed", error=str(result))
            elif isinstance(result, list):
                successful_operations += len([r for r in result if r.get("status") == "success"])
                failed_operations += len([r for r in result if r.get("status") != "success"])
        
        # Calculate metrics
        operations_per_second = successful_operations / total_time if total_time > 0 else 0
        error_rate = (failed_operations / (successful_operations + failed_operations)) * 100
        
        # Update performance monitor
        self.performance_monitor.metrics.requests_per_second = operations_per_second
        self.performance_monitor.metrics.concurrent_users_supported = concurrent_users
        self.performance_monitor.metrics.error_rate_percent = error_rate
        self.performance_monitor.update_resource_metrics()
        
        # Validate against healthcare standards
        compliance_status = self.performance_monitor.metrics.meets_healthcare_standards()
        
        test_result = {
            "test_name": "patient_registration_performance_load",
            "concurrent_users": concurrent_users,
            "operations_per_user": operations_per_user,
            "total_operations": successful_operations + failed_operations,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "total_time_seconds": total_time,
            "operations_per_second": operations_per_second,
            "error_rate_percent": error_rate,
            "performance_metrics": self.performance_monitor.metrics.calculate_averages(),
            "compliance_status": compliance_status,
            "requirements_met": {
                "throughput_requirement": operations_per_second >= self.config.min_requests_per_second,
                "error_rate_requirement": error_rate <= self.config.max_error_rate_percent,
                "patient_query_requirement": compliance_status.get("patient_queries_compliant", False),
                "memory_requirement": compliance_status.get("memory_usage_compliant", False),
                "cpu_requirement": compliance_status.get("cpu_usage_compliant", False)
            }
        }
        
        self.test_results["patient_registration_performance"] = test_result
        
        logger.info("Patient registration performance test completed",
                   operations_per_second=operations_per_second,
                   error_rate=error_rate,
                   requirements_met=all(test_result["requirements_met"].values()))
        
        return test_result
    
    async def _simulate_patient_registration_operations(
        self, 
        user_id: int, 
        operation_count: int
    ) -> List[Dict[str, Any]]:
        """Simulate patient registration operations for performance testing."""
        operations = []
        
        for op_id in range(operation_count):
            operation_start = time.time()
            
            try:
                # Simulate patient registration workflow
                async with HealthcareSessionManager(self.session_factory) as session:
                    # Create patient record
                    with self.performance_monitor.measure_operation("patient_query"):
                        patient_data = await self._create_test_patient(session, user_id, op_id)
                    
                    # Create immunization record
                    with self.performance_monitor.measure_operation("immunization_query"):
                        immunization_data = await self._create_test_immunization(
                            session, patient_data["id"], user_id, op_id
                        )
                    
                    # Simulate FHIR Bundle creation
                    with self.performance_monitor.measure_operation("fhir_operation"):
                        fhir_bundle = await self._create_fhir_bundle(
                            patient_data, immunization_data
                        )
                    
                    # Simulate audit logging
                    with self.performance_monitor.measure_operation("audit_log"):
                        await self._create_audit_log(session, user_id, op_id, "patient_registration")
                
                operation_time = (time.time() - operation_start) * 1000
                
                operations.append({
                    "user_id": user_id,
                    "operation_id": op_id,
                    "status": "success",
                    "operation_time_ms": operation_time,
                    "patient_created": True,
                    "immunization_created": True,
                    "fhir_bundle_created": len(fhir_bundle.get("entry", [])) > 0
                })
                
            except Exception as e:
                operation_time = (time.time() - operation_start) * 1000
                operations.append({
                    "user_id": user_id,
                    "operation_id": op_id,
                    "status": "error",
                    "operation_time_ms": operation_time,
                    "error": str(e)
                })
                
                logger.error("Patient registration operation failed",
                           user_id=user_id, operation_id=op_id, error=str(e))
        
        return operations
    
    async def _create_test_patient(
        self, 
        session: AsyncSession, 
        user_id: int, 
        op_id: int
    ) -> Dict[str, Any]:
        """Create test patient record for performance testing."""
        patient_id = f"test_patient_{user_id}_{op_id}_{int(time.time())}"
        
        # Simulate patient creation query
        query = text("""
            INSERT INTO patients (id, first_name, last_name, date_of_birth, mrn, created_at)
            VALUES (:id, :first_name, :last_name, :dob, :mrn, :created_at)
            ON CONFLICT (id) DO UPDATE SET
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name
            RETURNING id, first_name, last_name, mrn
        """)
        
        result = await session.execute(query, {
            "id": patient_id,
            "first_name": f"TestFirst{user_id}",
            "last_name": f"TestLast{op_id}",
            "dob": "1990-01-01",
            "mrn": f"MRN{user_id}{op_id}",
            "created_at": datetime.now(timezone.utc)
        })
        
        await session.commit()
        return {"id": patient_id, "mrn": f"MRN{user_id}{op_id}"}
    
    async def _create_test_immunization(
        self, 
        session: AsyncSession, 
        patient_id: str, 
        user_id: int, 
        op_id: int
    ) -> Dict[str, Any]:
        """Create test immunization record for performance testing."""
        immunization_id = f"test_immunization_{user_id}_{op_id}_{int(time.time())}"
        
        # Simulate immunization creation query
        query = text("""
            INSERT INTO immunizations (id, patient_id, vaccine_code, administration_date, created_at)
            VALUES (:id, :patient_id, :vaccine_code, :admin_date, :created_at)
            ON CONFLICT (id) DO UPDATE SET
                vaccine_code = EXCLUDED.vaccine_code
            RETURNING id, patient_id, vaccine_code
        """)
        
        result = await session.execute(query, {
            "id": immunization_id,
            "patient_id": patient_id,
            "vaccine_code": "COVID19",
            "admin_date": datetime.now(timezone.utc).date(),
            "created_at": datetime.now(timezone.utc)
        })
        
        await session.commit()
        return {"id": immunization_id, "patient_id": patient_id}
    
    async def _create_fhir_bundle(
        self, 
        patient_data: Dict[str, Any], 
        immunization_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create FHIR Bundle for performance testing."""
        bundle = {
            "resourceType": "Bundle",
            "id": f"bundle_{patient_data['id']}_{int(time.time())}",
            "type": "transaction",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": patient_data["id"],
                        "identifier": [
                            {
                                "type": {
                                    "coding": [
                                        {
                                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                            "code": "MR",
                                            "display": "Medical Record Number"
                                        }
                                    ]
                                },
                                "value": patient_data["mrn"]
                            }
                        ]
                    }
                },
                {
                    "resource": {
                        "resourceType": "Immunization",
                        "id": immunization_data["id"],
                        "status": "completed",
                        "vaccineCode": {
                            "coding": [
                                {
                                    "system": "http://hl7.org/fhir/sid/cvx",
                                    "code": "207",
                                    "display": "COVID-19 vaccine"
                                }
                            ]
                        },
                        "patient": {
                            "reference": f"Patient/{patient_data['id']}"
                        },
                        "occurrenceDateTime": datetime.now(timezone.utc).isoformat()
                    }
                }
            ]
        }
        
        # Validate bundle using FHIR optimizer
        validation_result = await self.fhir_optimizer.process_fhir_bundle_optimized(
            bundle, validate=True
        )
        
        return bundle
    
    async def _create_audit_log(
        self, 
        session: AsyncSession, 
        user_id: int, 
        op_id: int, 
        action: str
    ):
        """Create audit log entry for compliance testing."""
        query = text("""
            INSERT INTO audit_logs (
                id, event_type, user_id, action, outcome, timestamp, 
                aggregate_id, aggregate_type, soc2_category
            )
            VALUES (:id, :event_type, :user_id, :action, :outcome, :timestamp,
                    :aggregate_id, :aggregate_type, :soc2_category)
        """)
        
        await session.execute(query, {
            "id": f"audit_{user_id}_{op_id}_{int(time.time())}",
            "event_type": "performance_test",
            "user_id": f"test_user_{user_id}",
            "action": action,
            "outcome": "success",
            "timestamp": datetime.now(timezone.utc),
            "aggregate_id": f"test_aggregate_{user_id}_{op_id}",
            "aggregate_type": "performance_test",
            "soc2_category": "CC6.1"
        })
        
        await session.commit()
    
    async def run_immunization_processing_performance_test(
        self, 
        concurrent_users: int = 20,
        operations_per_user: int = 15
    ) -> Dict[str, Any]:
        """Run immunization processing performance test."""
        logger.info("Starting immunization processing performance test",
                   concurrent_users=concurrent_users,
                   operations_per_user=operations_per_user)
        
        start_time = time.time()
        tasks = []
        
        # Create concurrent immunization processing tasks
        for user_id in range(concurrent_users):
            task = asyncio.create_task(
                self._simulate_immunization_processing(user_id, operations_per_user)
            )
            tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Analyze results
        successful_operations = 0
        failed_operations = 0
        
        for result in results:
            if isinstance(result, Exception):
                failed_operations += operations_per_user
            elif isinstance(result, list):
                successful_operations += len([r for r in result if r.get("status") == "success"])
                failed_operations += len([r for r in result if r.get("status") != "success"])
        
        # Calculate performance metrics
        operations_per_second = successful_operations / total_time if total_time > 0 else 0
        error_rate = (failed_operations / (successful_operations + failed_operations)) * 100
        
        compliance_status = self.performance_monitor.metrics.meets_healthcare_standards()
        
        test_result = {
            "test_name": "immunization_processing_performance_load",
            "concurrent_users": concurrent_users,
            "operations_per_user": operations_per_user,
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "operations_per_second": operations_per_second,
            "error_rate_percent": error_rate,
            "total_time_seconds": total_time,
            "compliance_status": compliance_status,
            "requirements_met": {
                "immunization_query_requirement": compliance_status.get("immunization_queries_compliant", False),
                "throughput_requirement": operations_per_second >= self.config.min_requests_per_second,
                "error_rate_requirement": error_rate <= self.config.max_error_rate_percent
            }
        }
        
        self.test_results["immunization_processing_performance"] = test_result
        return test_result
    
    async def _simulate_immunization_processing(
        self, 
        user_id: int, 
        operation_count: int
    ) -> List[Dict[str, Any]]:
        """Simulate immunization processing operations."""
        operations = []
        
        for op_id in range(operation_count):
            try:
                async with HealthcareSessionManager(self.session_factory) as session:
                    # Query immunization history
                    with self.performance_monitor.measure_operation("immunization_query"):
                        immunizations = await self.query_optimizer.get_immunization_history_optimized(
                            f"patient_{user_id}_{op_id}"
                        )
                    
                    operations.append({
                        "user_id": user_id,
                        "operation_id": op_id,
                        "status": "success",
                        "immunizations_found": len(immunizations) if immunizations else 0
                    })
                    
            except Exception as e:
                operations.append({
                    "user_id": user_id,
                    "operation_id": op_id,
                    "status": "error",
                    "error": str(e)
                })
        
        return operations
    
    async def run_fhir_interoperability_performance_test(
        self, 
        concurrent_users: int = 15,
        bundles_per_user: int = 5
    ) -> Dict[str, Any]:
        """Run FHIR interoperability performance test."""
        logger.info("Starting FHIR interoperability performance test",
                   concurrent_users=concurrent_users,
                   bundles_per_user=bundles_per_user)
        
        start_time = time.time()
        tasks = []
        
        for user_id in range(concurrent_users):
            task = asyncio.create_task(
                self._simulate_fhir_operations(user_id, bundles_per_user)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Analyze FHIR processing results
        successful_bundles = 0
        failed_bundles = 0
        
        for result in results:
            if isinstance(result, Exception):
                failed_bundles += bundles_per_user
            elif isinstance(result, list):
                successful_bundles += len([r for r in result if r.get("status") == "success"])
                failed_bundles += len([r for r in result if r.get("status") != "success"])
        
        bundles_per_second = successful_bundles / total_time if total_time > 0 else 0
        error_rate = (failed_bundles / (successful_bundles + failed_bundles)) * 100
        
        compliance_status = self.performance_monitor.metrics.meets_healthcare_standards()
        
        test_result = {
            "test_name": "fhir_interoperability_performance_load",
            "concurrent_users": concurrent_users,
            "bundles_per_user": bundles_per_user,
            "successful_bundles": successful_bundles,
            "failed_bundles": failed_bundles,
            "bundles_per_second": bundles_per_second,
            "error_rate_percent": error_rate,
            "total_time_seconds": total_time,
            "compliance_status": compliance_status,
            "requirements_met": {
                "fhir_operations_requirement": compliance_status.get("fhir_operations_compliant", False),
                "throughput_requirement": bundles_per_second >= (self.config.min_requests_per_second / 4),
                "error_rate_requirement": error_rate <= self.config.max_error_rate_percent
            }
        }
        
        self.test_results["fhir_interoperability_performance"] = test_result
        return test_result
    
    async def _simulate_fhir_operations(
        self, 
        user_id: int, 
        bundle_count: int
    ) -> List[Dict[str, Any]]:
        """Simulate FHIR Bundle operations."""
        operations = []
        
        for bundle_id in range(bundle_count):
            try:
                # Create sample FHIR bundle
                bundle_data = self._create_sample_fhir_bundle(user_id, bundle_id)
                
                # Process bundle with performance monitoring
                with self.performance_monitor.measure_operation("fhir_operation"):
                    result = await self.fhir_optimizer.process_fhir_bundle_optimized(
                        bundle_data, validate=True
                    )
                
                operations.append({
                    "user_id": user_id,
                    "bundle_id": bundle_id,
                    "status": "success" if result["success"] else "failed",
                    "processing_time_ms": result["processing_time_ms"],
                    "entries_processed": result.get("processed_entries", 0)
                })
                
            except Exception as e:
                operations.append({
                    "user_id": user_id,
                    "bundle_id": bundle_id,
                    "status": "error",
                    "error": str(e)
                })
        
        return operations
    
    def _create_sample_fhir_bundle(self, user_id: int, bundle_id: int) -> Dict[str, Any]:
        """Create sample FHIR Bundle for testing."""
        return {
            "resourceType": "Bundle",
            "id": f"test-bundle-{user_id}-{bundle_id}",
            "type": "transaction",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": f"test-patient-{user_id}-{bundle_id}",
                        "name": [
                            {
                                "family": f"TestFamily{user_id}",
                                "given": [f"TestGiven{bundle_id}"]
                            }
                        ],
                        "gender": "unknown",
                        "birthDate": "1990-01-01"
                    }
                },
                {
                    "resource": {
                        "resourceType": "Immunization",
                        "id": f"test-immunization-{user_id}-{bundle_id}",
                        "status": "completed",
                        "vaccineCode": {
                            "coding": [
                                {
                                    "system": "http://hl7.org/fhir/sid/cvx",
                                    "code": "207",
                                    "display": "COVID-19 vaccine"
                                }
                            ]
                        },
                        "patient": {
                            "reference": f"Patient/test-patient-{user_id}-{bundle_id}"
                        },
                        "occurrenceDateTime": "2023-01-15"
                    }
                }
            ]
        }
    
    def get_comprehensive_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance test report."""
        overall_compliance = True
        performance_summary = {}
        
        for test_name, test_result in self.test_results.items():
            test_passed = all(test_result.get("requirements_met", {}).values())
            overall_compliance = overall_compliance and test_passed
            
            performance_summary[test_name] = {
                "passed": test_passed,
                "operations_per_second": test_result.get("operations_per_second", 0),
                "error_rate_percent": test_result.get("error_rate_percent", 0),
                "compliance_status": test_result.get("compliance_status", {})
            }
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_compliance": overall_compliance,
            "performance_summary": performance_summary,
            "system_metrics": {
                "peak_memory_mb": self.performance_monitor.metrics.peak_memory_mb,
                "peak_cpu_percent": self.performance_monitor.metrics.peak_cpu_percent,
                "total_operations": sum(
                    result.get("successful_operations", 0) + result.get("failed_operations", 0)
                    for result in self.test_results.values()
                )
            },
            "detailed_results": self.test_results
        }

# ============================================
# PYTEST FIXTURES FOR PERFORMANCE TESTING
# ============================================

@pytest.fixture(scope="session")
async def performance_test_framework():
    """Provide performance test framework for healthcare testing."""
    framework = HealthcarePerformanceTestFramework()
    await framework.initialize()
    
    yield framework
    
    await framework.cleanup()

@pytest.fixture(scope="function")
async def isolated_performance_session():
    """Provide isolated database session for performance testing."""
    session_factory = await get_isolated_session_factory()
    
    async with HealthcareSessionManager(session_factory) as session:
        yield session

# ============================================
# PERFORMANCE TEST UTILITIES
# ============================================

def validate_healthcare_performance_requirements(test_result: Dict[str, Any]) -> bool:
    """Validate test results against healthcare performance requirements."""
    requirements = [
        test_result.get("operations_per_second", 0) >= 100,
        test_result.get("error_rate_percent", 100) <= 1.0,
        test_result.get("compliance_status", {}).get("patient_queries_compliant", False),
        test_result.get("compliance_status", {}).get("memory_usage_compliant", False),
        test_result.get("compliance_status", {}).get("cpu_usage_compliant", False)
    ]
    
    return all(requirements)

def log_performance_metrics(test_name: str, test_result: Dict[str, Any]):
    """Log performance metrics for monitoring and compliance."""
    logger.info(
        f"Healthcare performance test completed: {test_name}",
        extra={
            "test_name": test_name,
            "operations_per_second": test_result.get("operations_per_second", 0),
            "error_rate_percent": test_result.get("error_rate_percent", 0),
            "concurrent_users": test_result.get("concurrent_users", 0),
            "total_operations": test_result.get("successful_operations", 0) + test_result.get("failed_operations", 0),
            "requirements_met": all(test_result.get("requirements_met", {}).values()),
            "compliance_framework": "SOC2_HIPAA_FHIR",
            "soc2_category": "CC7.1"  # System monitoring
        }
    )

async def cleanup_performance_test_data():
    """Clean up performance test data from database."""
    try:
        session_factory = await get_isolated_session_factory()
        async with HealthcareSessionManager(session_factory) as session:
            # Clean up test patients
            await session.execute(text("DELETE FROM patients WHERE id LIKE 'test_patient_%'"))
            # Clean up test immunizations
            await session.execute(text("DELETE FROM immunizations WHERE id LIKE 'test_immunization_%'"))
            # Clean up test audit logs
            await session.execute(text("DELETE FROM audit_logs WHERE id LIKE 'audit_%' AND event_type = 'performance_test'"))
            
            await session.commit()
            
        logger.info("Performance test data cleanup completed")
        
    except Exception as e:
        logger.error("Performance test data cleanup failed", error=str(e))