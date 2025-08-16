"""
Enterprise Healthcare Performance Test Fixes

SOC2 Type 2, HIPAA, FHIR R4, GDPR Compliant Performance Testing
Production-ready performance validation with enterprise-grade fixes.
"""

import pytest
import pytest_asyncio
import asyncio
import time
import gc
from typing import Dict, Any, List
import structlog

from app.tests.performance.performance_test_infrastructure import (
    HealthcarePerformanceTestFramework,
    HealthcarePerformanceTestConfig,
    validate_healthcare_performance_requirements,
    log_performance_metrics,
    cleanup_performance_test_data
)
from app.core.performance_optimization import get_performance_manager
from app.core.encryption_performance import get_encryption_manager

logger = structlog.get_logger()

# ============================================
# HEALTHCARE PERFORMANCE TEST CLASSES
# ============================================

@pytest.mark.asyncio
@pytest.mark.performance
class TestHealthcarePerformanceComprehensive:
    """Comprehensive healthcare performance testing with enterprise compliance."""
    
    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Setup
        self.framework = HealthcarePerformanceTestFramework()
        await self.framework.initialize()
        
        yield
        
        # Teardown
        await cleanup_performance_test_data()
        await self.framework.cleanup()
        gc.collect()
    
    async def test_patient_registration_performance_load(self):
        """Test patient registration performance under load with SOC2 compliance."""
        logger.info("Starting patient registration performance test")
        
        # Configuration for healthcare performance requirements
        test_config = {
            "concurrent_users": 25,
            "operations_per_user": 10,
            "max_response_time_ms": 2000,
            "min_throughput_ops_per_sec": 50,
            "max_error_rate_percent": 1.0
        }
        
        # Run performance test
        result = await self.framework.run_patient_registration_performance_test(
            concurrent_users=test_config["concurrent_users"],
            operations_per_user=test_config["operations_per_user"]
        )
        
        # Log performance metrics for compliance monitoring
        log_performance_metrics("patient_registration_performance", result)
        
        # Validate healthcare performance requirements
        assert result["successful_operations"] > 0, "No successful patient registration operations"
        assert result["error_rate_percent"] <= test_config["max_error_rate_percent"], \
            f"Error rate {result['error_rate_percent']}% exceeds threshold {test_config['max_error_rate_percent']}%"
        assert result["operations_per_second"] >= test_config["min_throughput_ops_per_sec"], \
            f"Throughput {result['operations_per_second']} ops/sec below requirement {test_config['min_throughput_ops_per_sec']}"
        
        # Validate compliance requirements
        compliance_status = result["compliance_status"]
        assert compliance_status.get("patient_queries_compliant", False), "Patient query performance non-compliant"
        assert compliance_status.get("memory_usage_compliant", False), "Memory usage non-compliant"
        assert compliance_status.get("cpu_usage_compliant", False), "CPU usage non-compliant"
        
        # Validate all requirements are met
        requirements_met = result["requirements_met"]
        assert all(requirements_met.values()), f"Performance requirements not met: {requirements_met}"
        
        logger.info("Patient registration performance test passed",
                   operations_per_second=result["operations_per_second"],
                   error_rate=result["error_rate_percent"])
    
    async def test_immunization_processing_performance_load(self):
        """Test immunization processing performance under load."""
        logger.info("Starting immunization processing performance test")
        
        test_config = {
            "concurrent_users": 20,
            "operations_per_user": 15,
            "max_response_time_ms": 1500,
            "min_throughput_ops_per_sec": 40,
            "max_error_rate_percent": 1.0
        }
        
        # Run immunization performance test
        result = await self.framework.run_immunization_processing_performance_test(
            concurrent_users=test_config["concurrent_users"],
            operations_per_user=test_config["operations_per_user"]
        )
        
        # Log metrics
        log_performance_metrics("immunization_processing_performance", result)
        
        # Validate requirements
        assert result["successful_operations"] > 0, "No successful immunization operations"
        assert result["error_rate_percent"] <= test_config["max_error_rate_percent"], \
            f"Error rate {result['error_rate_percent']}% exceeds threshold"
        assert result["operations_per_second"] >= test_config["min_throughput_ops_per_sec"], \
            f"Throughput {result['operations_per_second']} ops/sec below requirement"
        
        # Validate compliance
        compliance_status = result["compliance_status"]
        assert compliance_status.get("immunization_queries_compliant", False), \
            "Immunization query performance non-compliant"
        
        requirements_met = result["requirements_met"]
        assert all(requirements_met.values()), f"Requirements not met: {requirements_met}"
        
        logger.info("Immunization processing performance test passed")
    
    async def test_fhir_interoperability_performance_load(self):
        """Test FHIR R4 interoperability performance under load."""
        logger.info("Starting FHIR interoperability performance test")
        
        test_config = {
            "concurrent_users": 15,
            "bundles_per_user": 5,
            "max_response_time_ms": 3000,
            "min_throughput_bundles_per_sec": 10,
            "max_error_rate_percent": 1.0
        }
        
        # Run FHIR performance test
        result = await self.framework.run_fhir_interoperability_performance_test(
            concurrent_users=test_config["concurrent_users"],
            bundles_per_user=test_config["bundles_per_user"]
        )
        
        # Log metrics
        log_performance_metrics("fhir_interoperability_performance", result)
        
        # Validate FHIR requirements
        assert result["successful_bundles"] > 0, "No successful FHIR bundle processing"
        assert result["error_rate_percent"] <= test_config["max_error_rate_percent"], \
            f"FHIR error rate {result['error_rate_percent']}% exceeds threshold"
        assert result["bundles_per_second"] >= test_config["min_throughput_bundles_per_sec"], \
            f"FHIR throughput {result['bundles_per_second']} bundles/sec below requirement"
        
        # Validate FHIR R4 compliance
        compliance_status = result["compliance_status"]
        assert compliance_status.get("fhir_operations_compliant", False), \
            "FHIR operations performance non-compliant"
        
        requirements_met = result["requirements_met"]
        assert all(requirements_met.values()), f"FHIR requirements not met: {requirements_met}"
        
        logger.info("FHIR interoperability performance test passed")
    
    async def test_clinical_workflow_comprehensive_performance(self):
        """Test comprehensive clinical workflow performance."""
        logger.info("Starting clinical workflow comprehensive performance test")
        
        # Run multiple performance tests in sequence to simulate clinical workflows
        patient_result = await self.framework.run_patient_registration_performance_test(
            concurrent_users=15, operations_per_user=8
        )
        
        immunization_result = await self.framework.run_immunization_processing_performance_test(
            concurrent_users=12, operations_per_user=10
        )
        
        fhir_result = await self.framework.run_fhir_interoperability_performance_test(
            concurrent_users=10, bundles_per_user=3
        )
        
        # Validate comprehensive workflow performance
        total_operations = (
            patient_result["successful_operations"] +
            immunization_result["successful_operations"] +
            fhir_result["successful_bundles"]
        )
        
        total_time = max(
            patient_result["total_time_seconds"],
            immunization_result["total_time_seconds"],
            fhir_result["total_time_seconds"]
        )
        
        overall_throughput = total_operations / total_time if total_time > 0 else 0
        
        # Validate clinical workflow requirements
        assert total_operations > 0, "No successful clinical workflow operations"
        assert overall_throughput >= 30, f"Clinical workflow throughput {overall_throughput} ops/sec too low"
        
        # Validate all individual components meet requirements
        assert validate_healthcare_performance_requirements(patient_result), \
            "Patient registration performance requirements not met"
        assert validate_healthcare_performance_requirements(immunization_result), \
            "Immunization processing performance requirements not met"
        assert validate_healthcare_performance_requirements(fhir_result), \
            "FHIR interoperability performance requirements not met"
        
        logger.info("Clinical workflow comprehensive performance test passed",
                   total_operations=total_operations,
                   overall_throughput=overall_throughput)
    
    async def test_concurrent_operations_stress_performance(self):
        """Test concurrent operations under stress conditions."""
        logger.info("Starting concurrent operations stress test")
        
        # High-stress configuration
        stress_config = {
            "concurrent_users": 40,
            "operations_per_user": 12,
            "max_memory_mb": 1000,
            "max_cpu_percent": 80,
            "max_error_rate_percent": 2.0  # Higher tolerance for stress test
        }
        
        # Run stress test
        result = await self.framework.run_patient_registration_performance_test(
            concurrent_users=stress_config["concurrent_users"],
            operations_per_user=stress_config["operations_per_user"]
        )
        
        # Log stress test metrics
        log_performance_metrics("concurrent_operations_stress", result)
        
        # Validate stress test requirements (more lenient)
        assert result["successful_operations"] > 100, "Insufficient successful operations under stress"
        assert result["error_rate_percent"] <= stress_config["max_error_rate_percent"], \
            f"Stress test error rate {result['error_rate_percent']}% exceeds threshold"
        
        # Validate resource usage under stress
        performance_metrics = result["performance_metrics"]
        # Note: Using max() to get peak values from the metrics
        peak_memory = max(self.framework.performance_monitor.metrics.peak_memory_mb, 0)
        peak_cpu = max(self.framework.performance_monitor.metrics.peak_cpu_percent, 0)
        
        assert peak_memory <= stress_config["max_memory_mb"], \
            f"Memory usage {peak_memory}MB exceeds stress limit {stress_config['max_memory_mb']}MB"
        assert peak_cpu <= stress_config["max_cpu_percent"], \
            f"CPU usage {peak_cpu}% exceeds stress limit {stress_config['max_cpu_percent']}%"
        
        logger.info("Concurrent operations stress test passed",
                   concurrent_users=stress_config["concurrent_users"],
                   successful_operations=result["successful_operations"])

@pytest.mark.asyncio 
@pytest.mark.performance
class TestHealthcarePerformanceRegression:
    """Healthcare performance regression testing."""
    
    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self):
        """Setup and teardown for regression tests."""
        self.framework = HealthcarePerformanceTestFramework()
        await self.framework.initialize()
        
        yield
        
        await cleanup_performance_test_data()
        await self.framework.cleanup()
        gc.collect()
    
    async def test_performance_baseline_establishment(self):
        """Establish performance baselines for regression testing."""
        logger.info("Establishing performance baselines")
        
        # Run baseline performance test
        result = await self.framework.run_patient_registration_performance_test(
            concurrent_users=10, operations_per_user=5
        )
        
        # Validate baseline establishment
        assert result["successful_operations"] > 0, "Cannot establish baseline - no successful operations"
        assert result["operations_per_second"] > 0, "Cannot establish baseline - no throughput"
        
        # Store baseline metrics for future regression testing
        baseline_metrics = {
            "operations_per_second": result["operations_per_second"],
            "error_rate_percent": result["error_rate_percent"],
            "average_response_time_ms": result["performance_metrics"].get("avg_patient_query_ms", 0),
            "established_at": time.time()
        }
        
        # Validate baseline quality
        assert baseline_metrics["operations_per_second"] >= 25, "Baseline throughput too low"
        assert baseline_metrics["error_rate_percent"] <= 1.0, "Baseline error rate too high"
        
        logger.info("Performance baseline established", **baseline_metrics)
    
    async def test_memory_usage_performance_monitoring(self):
        """Test memory usage performance monitoring."""
        logger.info("Testing memory usage performance monitoring")
        
        initial_memory = self.framework.performance_monitor.metrics.peak_memory_mb
        
        # Run memory-intensive performance test
        result = await self.framework.run_patient_registration_performance_test(
            concurrent_users=20, operations_per_user=8
        )
        
        final_memory = self.framework.performance_monitor.metrics.peak_memory_mb
        memory_increase = final_memory - initial_memory
        
        # Validate memory performance
        assert result["successful_operations"] > 0, "No successful operations for memory test"
        assert final_memory <= 1000, f"Memory usage {final_memory}MB exceeds limit"
        assert memory_increase <= 500, f"Memory increase {memory_increase}MB too high"
        
        # Check for memory leaks
        gc.collect()  # Force garbage collection
        await asyncio.sleep(1)  # Allow cleanup
        
        post_gc_memory = self.framework.performance_monitor.metrics.peak_memory_mb
        memory_leak_threshold = 50  # MB
        
        if post_gc_memory - initial_memory > memory_leak_threshold:
            logger.warning("Potential memory leak detected",
                          initial=initial_memory,
                          final=final_memory,
                          post_gc=post_gc_memory)
        
        logger.info("Memory usage performance monitoring passed",
                   initial_memory=initial_memory,
                   peak_memory=final_memory,
                   memory_increase=memory_increase)
    
    async def test_database_performance_optimization_validation(self):
        """Validate database performance optimizations."""
        logger.info("Testing database performance optimization validation")
        
        # Get performance manager for database optimization testing
        performance_manager = get_performance_manager()
        await performance_manager.initialize()
        
        # Run database-intensive performance test
        result = await self.framework.run_patient_registration_performance_test(
            concurrent_users=15, operations_per_user=10
        )
        
        # Validate database performance
        assert result["successful_operations"] > 0, "No successful database operations"
        performance_metrics = result["performance_metrics"]
        
        # Check database query performance
        avg_patient_query_ms = performance_metrics.get("avg_patient_query_ms", 1000)
        avg_immunization_query_ms = performance_metrics.get("avg_immunization_query_ms", 1000)
        
        assert avg_patient_query_ms <= 500, f"Patient queries {avg_patient_query_ms}ms too slow"
        assert avg_immunization_query_ms <= 300, f"Immunization queries {avg_immunization_query_ms}ms too slow"
        
        # Validate connection pool performance
        connection_metrics = performance_manager.connection_pool.get_pool_metrics() if hasattr(performance_manager, 'connection_pool') else {}
        
        # Basic validation even if connection pool not available
        assert result["error_rate_percent"] <= 1.0, "Database error rate too high"
        
        logger.info("Database performance optimization validation passed",
                   avg_patient_query_ms=avg_patient_query_ms,
                   avg_immunization_query_ms=avg_immunization_query_ms)

@pytest.mark.asyncio
@pytest.mark.performance  
class TestHealthcarePerformanceScalability:
    """Healthcare performance scalability testing."""
    
    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self):
        """Setup and teardown for scalability tests."""
        self.framework = HealthcarePerformanceTestFramework()
        await self.framework.initialize()
        
        yield
        
        await cleanup_performance_test_data()
        await self.framework.cleanup()
        gc.collect()
    
    async def test_user_scalability_performance_validation(self):
        """Test user scalability performance validation."""
        logger.info("Testing user scalability performance validation")
        
        # Test scalability with increasing user loads
        user_loads = [5, 10, 15, 20, 25]
        results = []
        
        for user_count in user_loads:
            logger.info(f"Testing with {user_count} concurrent users")
            
            result = await self.framework.run_patient_registration_performance_test(
                concurrent_users=user_count,
                operations_per_user=5
            )
            
            results.append({
                "user_count": user_count,
                "operations_per_second": result["operations_per_second"],
                "error_rate_percent": result["error_rate_percent"],
                "successful_operations": result["successful_operations"]
            })
        
        # Validate scalability characteristics
        assert len(results) == len(user_loads), "Missing scalability test results"
        
        # Check that system handles increasing load reasonably
        max_error_rate = max(r["error_rate_percent"] for r in results)
        min_throughput = min(r["operations_per_second"] for r in results)
        
        assert max_error_rate <= 2.0, f"Maximum error rate {max_error_rate}% too high under load"
        assert min_throughput >= 20, f"Minimum throughput {min_throughput} ops/sec too low"
        
        # Validate that the system scales reasonably (throughput doesn't degrade severely)
        first_result = results[0]
        last_result = results[-1]
        
        throughput_ratio = last_result["operations_per_second"] / first_result["operations_per_second"]
        user_ratio = last_result["user_count"] / first_result["user_count"]
        
        # Throughput should scale at least 50% as well as user count
        scaling_efficiency = throughput_ratio / user_ratio
        assert scaling_efficiency >= 0.5, f"Poor scaling efficiency: {scaling_efficiency}"
        
        logger.info("User scalability performance validation passed",
                   max_users_tested=max(user_loads),
                   scaling_efficiency=scaling_efficiency)
    
    async def test_data_volume_scalability_performance(self):
        """Test data volume scalability performance."""
        logger.info("Testing data volume scalability performance")
        
        # Test with different operation volumes per user
        operation_volumes = [3, 6, 9, 12, 15]
        results = []
        
        for ops_per_user in operation_volumes:
            logger.info(f"Testing with {ops_per_user} operations per user")
            
            result = await self.framework.run_patient_registration_performance_test(
                concurrent_users=10,
                operations_per_user=ops_per_user
            )
            
            results.append({
                "operations_per_user": ops_per_user,
                "total_operations": result["successful_operations"],
                "operations_per_second": result["operations_per_second"],
                "error_rate_percent": result["error_rate_percent"]
            })
        
        # Validate data volume scalability
        assert len(results) == len(operation_volumes), "Missing data volume test results"
        
        # Check that system handles increasing data volume
        max_error_rate = max(r["error_rate_percent"] for r in results)
        min_throughput = min(r["operations_per_second"] for r in results)
        
        assert max_error_rate <= 2.0, f"Maximum error rate {max_error_rate}% too high with data volume"
        assert min_throughput >= 15, f"Minimum throughput {min_throughput} ops/sec too low with data volume"
        
        # Validate linear scaling characteristics
        total_operations = [r["total_operations"] for r in results]
        assert all(ops > 0 for ops in total_operations), "Some tests had no successful operations"
        
        # Check that total operations scale with volume
        first_total = total_operations[0]
        last_total = total_operations[-1]
        volume_ratio = operation_volumes[-1] / operation_volumes[0]
        operations_ratio = last_total / first_total
        
        # Operations should scale at least 70% as well as volume
        volume_efficiency = operations_ratio / volume_ratio
        assert volume_efficiency >= 0.7, f"Poor data volume scaling: {volume_efficiency}"
        
        logger.info("Data volume scalability performance passed",
                   max_operations_per_user=max(operation_volumes),
                   volume_efficiency=volume_efficiency)

# ============================================
# COMPREHENSIVE PERFORMANCE TEST SUITE
# ============================================

@pytest.mark.asyncio
@pytest.mark.performance
async def test_comprehensive_performance_suite():
    """Run comprehensive healthcare performance test suite."""
    logger.info("Starting comprehensive healthcare performance test suite")
    
    framework = HealthcarePerformanceTestFramework()
    await framework.initialize()
    
    try:
        # Run all performance tests
        patient_result = await framework.run_patient_registration_performance_test(
            concurrent_users=20, operations_per_user=8
        )
        
        immunization_result = await framework.run_immunization_processing_performance_test(
            concurrent_users=15, operations_per_user=10
        )
        
        fhir_result = await framework.run_fhir_interoperability_performance_test(
            concurrent_users=12, bundles_per_user=4
        )
        
        # Generate comprehensive report
        comprehensive_report = framework.get_comprehensive_performance_report()
        
        # Validate comprehensive suite results
        assert comprehensive_report["overall_compliance"], "Overall performance compliance failed"
        assert patient_result["successful_operations"] > 0, "Patient operations failed"
        assert immunization_result["successful_operations"] > 0, "Immunization operations failed"
        assert fhir_result["successful_bundles"] > 0, "FHIR operations failed"
        
        # Log comprehensive results
        logger.info("Comprehensive performance test suite completed",
                   overall_compliance=comprehensive_report["overall_compliance"],
                   total_operations=comprehensive_report["system_metrics"]["total_operations"])
        
        # Validate enterprise healthcare requirements
        assert validate_healthcare_performance_requirements(patient_result), \
            "Patient performance requirements not met"
        assert validate_healthcare_performance_requirements(immunization_result), \
            "Immunization performance requirements not met"
        assert validate_healthcare_performance_requirements(fhir_result), \
            "FHIR performance requirements not met"
        
    finally:
        await cleanup_performance_test_data()
        await framework.cleanup()
        gc.collect()
    
    logger.info("Comprehensive healthcare performance test suite passed")