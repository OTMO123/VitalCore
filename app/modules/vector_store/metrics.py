"""
Vector Store Prometheus Metrics

Enterprise-grade monitoring and metrics collection for vector database operations
with healthcare-specific KPIs and SOC2 compliance tracking.
"""

from prometheus_client import Counter, Histogram, Gauge, Info
import structlog
from typing import Dict, Any
from datetime import datetime, timezone

logger = structlog.get_logger(__name__)

# Vector Store Operation Metrics
vector_operations_total = Counter(
    'vector_store_operations_total',
    'Total number of vector store operations',
    ['operation_type', 'status', 'collection']
)

vector_operation_duration = Histogram(
    'vector_store_operation_duration_seconds',
    'Duration of vector store operations in seconds',
    ['operation_type', 'collection'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

vector_search_results = Histogram(
    'vector_store_search_results_count',
    'Number of results returned by vector search',
    ['collection', 'similarity_threshold'],
    buckets=[0, 1, 5, 10, 25, 50, 100, 250, 500, 1000]
)

# Circuit Breaker Metrics
circuit_breaker_state = Gauge(
    'vector_store_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=half-open, 2=open)',
    ['service_name']
)

circuit_breaker_failures = Counter(
    'vector_store_circuit_breaker_failures_total',
    'Total number of circuit breaker failures',
    ['service_name', 'failure_type']
)

circuit_breaker_trips = Counter(
    'vector_store_circuit_breaker_trips_total',
    'Total number of circuit breaker trips',
    ['service_name']
)

# Connection and Health Metrics
vector_store_connections = Gauge(
    'vector_store_connections_active',
    'Number of active vector store connections',
    ['host', 'port']
)

vector_store_health = Gauge(
    'vector_store_health_status',
    'Vector store health status (1=healthy, 0=unhealthy)',
    ['service_name', 'component']
)

# Healthcare-Specific Metrics
patient_vectors_indexed = Counter(
    'healthcare_patient_vectors_indexed_total',
    'Total number of patient vectors indexed',
    ['anonymization_level', 'medical_category']
)

phi_access_events = Counter(
    'healthcare_phi_vector_access_total',
    'Total PHI vector access events for audit',
    ['access_type', 'user_role', 'compliance_level']
)

clinical_similarity_searches = Counter(
    'healthcare_clinical_similarity_searches_total',
    'Total clinical similarity searches performed',
    ['search_type', 'medical_specialty', 'success']
)

# Performance and Cache Metrics
vector_cache_hits = Counter(
    'vector_store_cache_hits_total',
    'Total number of vector cache hits',
    ['cache_type']
)

vector_cache_misses = Counter(
    'vector_store_cache_misses_total',
    'Total number of vector cache misses',
    ['cache_type']
)

vector_index_size = Gauge(
    'vector_store_index_size_bytes',
    'Size of vector index in bytes',
    ['collection', 'index_type']
)

# Service Information
vector_store_info = Info(
    'vector_store_info',
    'Vector store service information'
)

class VectorStoreMetrics:
    """
    Centralized metrics collection for vector store operations.
    
    Provides enterprise-grade monitoring with healthcare-specific
    metrics and SOC2 compliance tracking.
    """
    
    def __init__(self, service_name: str = "milvus_vector_store"):
        self.service_name = service_name
        self.logger = logger.bind(component="VectorStoreMetrics")
        
        # Initialize service info
        vector_store_info.info({
            'service_name': service_name,
            'version': '1.0.0',
            'initialized_at': datetime.now(timezone.utc).isoformat()
        })
        
        self.logger.info("Vector store metrics initialized", service_name=service_name)
    
    def record_operation(self, operation_type: str, collection: str, 
                        duration: float, status: str = "success"):
        """Record vector store operation metrics"""
        vector_operations_total.labels(
            operation_type=operation_type,
            status=status,
            collection=collection
        ).inc()
        
        vector_operation_duration.labels(
            operation_type=operation_type,
            collection=collection
        ).observe(duration)
    
    def record_search(self, collection: str, result_count: int, 
                     similarity_threshold: float = 0.8, success: bool = True):
        """Record vector search metrics"""
        vector_search_results.labels(
            collection=collection,
            similarity_threshold=str(similarity_threshold)
        ).observe(result_count)
        
        vector_operations_total.labels(
            operation_type="search",
            status="success" if success else "failure",
            collection=collection
        ).inc()
    
    def update_circuit_breaker_state(self, state: str):
        """Update circuit breaker state metric"""
        state_mapping = {"closed": 0, "half_open": 1, "open": 2}
        circuit_breaker_state.labels(service_name=self.service_name).set(
            state_mapping.get(state, -1)
        )
    
    def record_circuit_breaker_failure(self, failure_type: str):
        """Record circuit breaker failure"""
        circuit_breaker_failures.labels(
            service_name=self.service_name,
            failure_type=failure_type
        ).inc()
    
    def record_circuit_breaker_trip(self):
        """Record circuit breaker trip"""
        circuit_breaker_trips.labels(service_name=self.service_name).inc()
    
    def update_connection_status(self, host: str, port: int, active: bool):
        """Update connection status"""
        vector_store_connections.labels(host=host, port=str(port)).set(1 if active else 0)
    
    def update_health_status(self, component: str, healthy: bool):
        """Update health status"""
        vector_store_health.labels(
            service_name=self.service_name,
            component=component
        ).set(1 if healthy else 0)
    
    def record_patient_indexing(self, count: int, anonymization_level: str, 
                               medical_category: str):
        """Record patient vector indexing for healthcare compliance"""
        for _ in range(count):
            patient_vectors_indexed.labels(
                anonymization_level=anonymization_level,
                medical_category=medical_category
            ).inc()
    
    def record_phi_access(self, access_type: str, user_role: str, 
                         compliance_level: str):
        """Record PHI vector access for HIPAA audit"""
        phi_access_events.labels(
            access_type=access_type,
            user_role=user_role,
            compliance_level=compliance_level
        ).inc()
    
    def record_clinical_search(self, search_type: str, medical_specialty: str, 
                              success: bool):
        """Record clinical similarity search"""
        clinical_similarity_searches.labels(
            search_type=search_type,
            medical_specialty=medical_specialty,
            success="success" if success else "failure"
        ).inc()
    
    def record_cache_hit(self, cache_type: str = "query"):
        """Record cache hit"""
        vector_cache_hits.labels(cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_type: str = "query"):
        """Record cache miss"""
        vector_cache_misses.labels(cache_type=cache_type).inc()
    
    def update_index_size(self, collection: str, index_type: str, size_bytes: int):
        """Update vector index size"""
        vector_index_size.labels(
            collection=collection,
            index_type=index_type
        ).set(size_bytes)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary"""
        return {
            "service_name": self.service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "circuit_breaker_state": circuit_breaker_state._value._value if hasattr(circuit_breaker_state, '_value') else 0,
            "total_operations": vector_operations_total._value._value if hasattr(vector_operations_total, '_value') else 0,
            "health_status": "healthy"  # Can be enhanced with actual health checks
        }

# Global metrics instance
vector_metrics = VectorStoreMetrics()