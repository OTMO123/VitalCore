"""
Enterprise Healthcare Performance Test Configuration

Optimized configuration for SOC2 Type II, HIPAA, FHIR R4, and GDPR compliance
in production-ready healthcare deployments.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import os


@dataclass
class EnterpriseTestConfig:
    """Enterprise-grade test configuration for healthcare performance testing."""
    
    # Test execution limits for stability
    max_concurrent_users: int = 10
    max_operations_per_user: int = 5
    max_test_duration_seconds: int = 120
    
    # Database connection limits
    max_db_connections: int = 20
    db_connection_timeout: int = 30
    
    # Encryption performance settings
    encryption_cache_size: int = 1000
    pbkdf2_iterations_testing: int = 10000  # Reduced for testing
    pbkdf2_iterations_production: int = 100000
    
    # SOC2 compliance thresholds
    max_response_time_ms: float = 3000.0
    max_p95_response_time_ms: float = 5000.0
    max_error_rate_percent: float = 2.0
    min_availability_percent: float = 99.0
    
    # HIPAA compliance settings
    audit_every_operation: bool = True
    encrypt_all_phi: bool = True
    log_access_attempts: bool = True
    
    # Performance optimization flags
    enable_encryption_cache: bool = True
    enable_connection_pooling: bool = True
    enable_query_optimization: bool = True
    
    # Test scenarios configuration
    test_scenarios: Dict[str, dict] = None
    
    def __post_init__(self):
        """Initialize default test scenarios."""
        if self.test_scenarios is None:
            self.test_scenarios = {
                "patient_registration": {
                    "user_count": min(self.max_concurrent_users, 8),
                    "operations_per_user": min(self.max_operations_per_user, 3),
                    "duration_seconds": min(self.max_test_duration_seconds, 60),
                    "success_criteria": {
                        "patient_operation_time": 2.5,
                        "p95_response_time": 4.0,
                        "error_rate_percent": 2.0,
                        "transactions_per_second": 2.0
                    }
                },
                "immunization_processing": {
                    "user_count": min(self.max_concurrent_users, 6),
                    "operations_per_user": min(self.max_operations_per_user, 4),
                    "duration_seconds": min(self.max_test_duration_seconds, 45),
                    "success_criteria": {
                        "immunization_operation_time": 2.0,
                        "p95_response_time": 3.5,
                        "error_rate_percent": 1.5,
                        "transactions_per_second": 3.0
                    }
                },
                "fhir_interoperability": {
                    "user_count": min(self.max_concurrent_users, 5),
                    "operations_per_user": min(self.max_operations_per_user, 2),
                    "duration_seconds": min(self.max_test_duration_seconds, 90),
                    "success_criteria": {
                        "fhir_bundle_processing_time": 4.0,
                        "p95_response_time": 6.0,
                        "error_rate_percent": 3.0,
                        "transactions_per_second": 1.5
                    }
                },
                "concurrent_operations": {
                    "user_count": self.max_concurrent_users,
                    "operations_per_user": min(self.max_operations_per_user, 3),
                    "duration_seconds": min(self.max_test_duration_seconds, 120),
                    "success_criteria": {
                        "concurrent_users_supported": self.max_concurrent_users,
                        "p95_response_time": self.max_p95_response_time_ms / 1000.0,  # Convert to seconds
                        "p99_response_time": (self.max_p95_response_time_ms * 1.2) / 1000.0,  # 20% higher than P95
                        "error_rate_percent": self.max_error_rate_percent,
                        "transactions_per_second": 1.0,
                        "memory_usage_mb": 1024,  # 1GB memory limit
                        "cpu_usage_percent": 80.0  # 80% CPU limit
                    }
                }
            }


def get_enterprise_config() -> EnterpriseTestConfig:
    """Get enterprise configuration based on environment."""
    
    # Check if running in CI/CD or test environment
    is_ci = os.getenv("CI", "false").lower() == "true"
    is_testing = os.getenv("TESTING", "false").lower() == "true"
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if is_ci or is_testing or environment == "test":
        # CI/CD optimized configuration
        return EnterpriseTestConfig(
            max_concurrent_users=5,
            max_operations_per_user=3,
            max_test_duration_seconds=60,
            max_db_connections=10,
            encryption_cache_size=500,
            max_response_time_ms=5000.0,  # More lenient for CI
            max_error_rate_percent=5.0,   # More lenient for CI
            min_availability_percent=95.0  # More lenient for CI
        )
    elif environment == "production":
        # Production-grade configuration
        return EnterpriseTestConfig(
            max_concurrent_users=25,
            max_operations_per_user=10,
            max_test_duration_seconds=300,
            max_db_connections=50,
            encryption_cache_size=2000,
            max_response_time_ms=2000.0,
            max_error_rate_percent=1.0,
            min_availability_percent=99.9
        )
    else:
        # Development/default configuration
        return EnterpriseTestConfig()


# Global configuration instance
ENTERPRISE_CONFIG = get_enterprise_config()


def get_scenario_config(scenario_name: str) -> dict:
    """Get configuration for a specific test scenario."""
    return ENTERPRISE_CONFIG.test_scenarios.get(scenario_name, {})


def is_performance_compliant(metrics: dict, scenario_name: str) -> tuple[bool, List[str]]:
    """Check if performance metrics meet enterprise compliance standards."""
    scenario_config = get_scenario_config(scenario_name)
    success_criteria = scenario_config.get("success_criteria", {})
    
    violations = []
    
    for criterion, threshold in success_criteria.items():
        metric_value = metrics.get(criterion)
        if metric_value is None:
            continue
            
        if criterion in ["patient_operation_time", "immunization_operation_time", 
                        "fhir_bundle_processing_time", "p95_response_time", "p99_response_time", 
                        "error_rate_percent", "memory_usage_mb", "cpu_usage_percent"]:
            if metric_value > threshold:
                violations.append(f"{criterion}: {metric_value} exceeds threshold {threshold}")
        elif criterion in ["transactions_per_second", "concurrent_users_supported"]:
            if metric_value < threshold:
                violations.append(f"{criterion}: {metric_value} below threshold {threshold}")
    
    return len(violations) == 0, violations