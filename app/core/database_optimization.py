"""
Database Query Optimization for Healthcare Records

Advanced database optimization strategies for production performance:
- Optimized patient lookup queries with composite indexes
- Database connection pool tuning and management
- Query performance monitoring and optimization
- Cache-friendly query patterns
- Database maintenance and optimization procedures

This module implements production-grade database optimizations
specifically designed for healthcare data access patterns.
"""

import asyncio
import time
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import text, Index, select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import Select
import structlog

from app.core.database_unified import get_db, Patient, ClinicalDocument, Consent
from app.core.config import get_settings

logger = structlog.get_logger()


class QueryOptimizationType(str, Enum):
    """Types of query optimizations available."""
    INDEX_OPTIMIZATION = "index_optimization"
    QUERY_REWRITE = "query_rewrite"
    CONNECTION_POOLING = "connection_pooling"
    CACHING = "caching"
    BATCHING = "batching"


@dataclass
class QueryPerformanceMetrics:
    """Performance metrics for database queries."""
    query_type: str
    execution_time_ms: float
    rows_returned: int
    connection_pool_size: int
    active_connections: int
    cache_hit: bool = False
    optimization_applied: Optional[str] = None


class DatabaseOptimizer:
    """Database query optimization manager."""
    
    def __init__(self):
        self.settings = get_settings()
        self.performance_metrics: List[QueryPerformanceMetrics] = []
        self.query_cache: Dict[str, Any] = {}
        self.cache_ttl: int = 300  # 5 minutes
        
    async def get_optimized_session(self) -> AsyncSession:
        """Get database session with optimized settings."""
        async for session in get_db():
            # Configure session for optimal performance
            await session.execute(text("SET statement_timeout = '30s'"))
            await session.execute(text("SET lock_timeout = '10s'"))
            await session.execute(text("SET idle_in_transaction_session_timeout = '60s'"))
            return session


class PatientLookupOptimizer:
    """Optimized patient lookup queries for production performance."""
    
    def __init__(self, db_optimizer: DatabaseOptimizer):
        self.db_optimizer = db_optimizer
        
    async def lookup_patient_by_mrn(self, mrn: str, session: AsyncSession) -> Optional[Patient]:
        """Optimized patient lookup by MRN with indexing."""
        start_time = time.time()
        
        try:
            # Use index-optimized query
            query = select(Patient).where(
                and_(
                    Patient.mrn == mrn,
                    Patient.active == True,
                    Patient.soft_deleted_at.is_(None)
                )
            ).options(
                # Optimize loading strategy
                selectinload(Patient.clinical_workflows)
            )
            
            result = await session.execute(query)
            patient = result.scalar_one_or_none()
            
            # Record performance metrics
            execution_time = (time.time() - start_time) * 1000
            
            metrics = QueryPerformanceMetrics(
                query_type="patient_lookup_by_mrn",
                execution_time_ms=execution_time,
                rows_returned=1 if patient else 0,
                connection_pool_size=session.bind.pool.size(),
                active_connections=session.bind.pool.checkedout(),
                optimization_applied="mrn_index"
            )
            
            self.db_optimizer.performance_metrics.append(metrics)
            
            if execution_time > 100:  # Log slow queries
                logger.warning(
                    "Slow patient lookup by MRN",
                    mrn=mrn,
                    execution_time_ms=execution_time
                )
            
            return patient
            
        except Exception as e:
            logger.error("Patient lookup by MRN failed", mrn=mrn, error=str(e))
            raise
    
    async def lookup_patient_by_external_id(self, external_id: str, session: AsyncSession) -> Optional[Patient]:
        """Optimized patient lookup by external ID."""
        start_time = time.time()
        
        try:
            # Cache key for this lookup
            cache_key = f"patient_external_id:{external_id}"
            
            # Check cache first
            if cache_key in self.db_optimizer.query_cache:
                cached_result = self.db_optimizer.query_cache[cache_key]
                if cached_result["timestamp"] > datetime.utcnow() - timedelta(seconds=self.db_optimizer.cache_ttl):
                    metrics = QueryPerformanceMetrics(
                        query_type="patient_lookup_by_external_id",
                        execution_time_ms=1.0,  # Cache hit is very fast
                        rows_returned=1 if cached_result["data"] else 0,
                        connection_pool_size=0,
                        active_connections=0,
                        cache_hit=True
                    )
                    self.db_optimizer.performance_metrics.append(metrics)
                    return cached_result["data"]
            
            # Execute optimized query
            query = select(Patient).where(
                and_(
                    Patient.external_id == external_id,
                    Patient.active == True,
                    Patient.soft_deleted_at.is_(None)
                )
            ).options(
                selectinload(Patient.clinical_workflows)
            )
            
            result = await session.execute(query)
            patient = result.scalar_one_or_none()
            
            # Cache the result
            self.db_optimizer.query_cache[cache_key] = {
                "data": patient,
                "timestamp": datetime.utcnow()
            }
            
            # Record metrics
            execution_time = (time.time() - start_time) * 1000
            metrics = QueryPerformanceMetrics(
                query_type="patient_lookup_by_external_id",
                execution_time_ms=execution_time,
                rows_returned=1 if patient else 0,
                connection_pool_size=session.bind.pool.size(),
                active_connections=session.bind.pool.checkedout(),
                optimization_applied="external_id_index_with_cache"
            )
            
            self.db_optimizer.performance_metrics.append(metrics)
            
            return patient
            
        except Exception as e:
            logger.error("Patient lookup by external ID failed", external_id=external_id, error=str(e))
            raise
    
    async def search_patients_optimized(
        self,
        session: AsyncSession,
        search_filters: Dict[str, Any],
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Patient], int]:
        """Optimized patient search with multiple filters."""
        start_time = time.time()
        
        try:
            # Build base query with optimal joins
            base_query = select(Patient).where(
                and_(
                    Patient.active == True,
                    Patient.soft_deleted_at.is_(None)
                )
            )
            
            # Apply filters efficiently
            conditions = []
            
            if mrn := search_filters.get("mrn"):
                conditions.append(Patient.mrn.ilike(f"%{mrn}%"))
            
            if external_id := search_filters.get("external_id"):
                conditions.append(Patient.external_id == external_id)
            
            if gender := search_filters.get("gender"):
                conditions.append(Patient.gender == gender)
            
            if tenant_id := search_filters.get("tenant_id"):
                conditions.append(Patient.tenant_id == tenant_id)
            
            if organization_id := search_filters.get("organization_id"):
                conditions.append(Patient.organization_id == organization_id)
            
            # Date range filter for created_at
            if date_from := search_filters.get("created_from"):
                conditions.append(Patient.created_at >= date_from)
            
            if date_to := search_filters.get("created_to"):
                conditions.append(Patient.created_at <= date_to)
            
            # Apply all conditions
            if conditions:
                base_query = base_query.where(and_(*conditions))
            
            # Count query for pagination
            count_query = select(func.count()).select_from(
                base_query.subquery()
            )
            
            # Main query with pagination and optimization
            search_query = base_query.options(
                selectinload(Patient.clinical_workflows)
            ).order_by(
                Patient.created_at.desc()  # Most recent first
            ).limit(limit).offset(offset)
            
            # Execute both queries concurrently
            count_result, search_result = await asyncio.gather(
                session.execute(count_query),
                session.execute(search_query)
            )
            
            total_count = count_result.scalar()
            patients = search_result.scalars().all()
            
            # Record performance metrics
            execution_time = (time.time() - start_time) * 1000
            metrics = QueryPerformanceMetrics(
                query_type="patient_search_optimized",
                execution_time_ms=execution_time,
                rows_returned=len(patients),
                connection_pool_size=session.bind.pool.size(),
                active_connections=session.bind.pool.checkedout(),
                optimization_applied="multi_filter_with_pagination"
            )
            
            self.db_optimizer.performance_metrics.append(metrics)
            
            if execution_time > 500:  # Log slow searches
                logger.warning(
                    "Slow patient search",
                    filters=search_filters,
                    execution_time_ms=execution_time,
                    result_count=len(patients)
                )
            
            return patients, total_count
            
        except Exception as e:
            logger.error("Patient search failed", filters=search_filters, error=str(e))
            raise
    
    async def bulk_lookup_patients(
        self,
        session: AsyncSession,
        patient_ids: List[uuid.UUID]
    ) -> List[Patient]:
        """Optimized bulk patient lookup."""
        start_time = time.time()
        
        try:
            # Use single query with IN clause for efficiency
            query = select(Patient).where(
                and_(
                    Patient.id.in_(patient_ids),
                    Patient.active == True,
                    Patient.soft_deleted_at.is_(None)
                )
            ).options(
                selectinload(Patient.clinical_workflows)
            ).order_by(Patient.created_at.desc())
            
            result = await session.execute(query)
            patients = result.scalars().all()
            
            # Record metrics
            execution_time = (time.time() - start_time) * 1000
            metrics = QueryPerformanceMetrics(
                query_type="bulk_patient_lookup",
                execution_time_ms=execution_time,
                rows_returned=len(patients),
                connection_pool_size=session.bind.pool.size(),
                active_connections=session.bind.pool.checkedout(),
                optimization_applied="bulk_in_clause"
            )
            
            self.db_optimizer.performance_metrics.append(metrics)
            
            return patients
            
        except Exception as e:
            logger.error("Bulk patient lookup failed", patient_count=len(patient_ids), error=str(e))
            raise


class ConnectionPoolOptimizer:
    """Database connection pool optimization and tuning."""
    
    def __init__(self):
        self.settings = get_settings()
        
    def get_optimized_engine_config(self) -> Dict[str, Any]:
        """Get optimized database engine configuration."""
        return {
            # Connection pool settings
            "poolclass": QueuePool,
            "pool_size": int(self.settings.db_pool_size_min or 10),
            "max_overflow": int(self.settings.db_pool_size_max or 50) - int(self.settings.db_pool_size_min or 10),
            "pool_pre_ping": self.settings.db_pool_pre_ping or True,
            "pool_recycle": int(self.settings.db_pool_recycle_seconds or 3600),
            
            # Connection timeouts
            "connect_args": {
                "connect_timeout": int(self.settings.db_connection_timeout or 30),
                "server_settings": {
                    "application_name": "healthcare_records_backend",
                    "statement_timeout": "30s",
                    "lock_timeout": "10s",
                    "idle_in_transaction_session_timeout": "60s",
                }
            },
            
            # Performance optimizations
            "echo": False,  # Disable SQL logging in production
            "future": True,  # Use SQLAlchemy 2.0 style
            "query_cache_size": 1200,  # Increase query cache
        }
    
    async def monitor_connection_pool(self, engine) -> Dict[str, Any]:
        """Monitor connection pool performance."""
        pool = engine.pool
        
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
            "utilization_percent": (pool.checkedout() / pool.size()) * 100 if pool.size() > 0 else 0
        }


class QueryOptimizationIndexes:
    """Database index recommendations and management."""
    
    @staticmethod
    def get_patient_lookup_indexes() -> List[str]:
        """Get SQL statements for patient lookup optimization indexes."""
        return [
            # Composite index for active patient lookups
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patients_active_lookup 
            ON patients (active, soft_deleted_at, mrn) 
            WHERE active = true AND soft_deleted_at IS NULL;
            """,
            
            # Index for external ID lookups
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patients_external_id_active 
            ON patients (external_id, active) 
            WHERE active = true AND soft_deleted_at IS NULL;
            """,
            
            # Composite index for tenant-based queries
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patients_tenant_org 
            ON patients (tenant_id, organization_id, active) 
            WHERE active = true AND soft_deleted_at IS NULL;
            """,
            
            # Index for date-based queries
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patients_created_at_active 
            ON patients (created_at DESC, active) 
            WHERE active = true AND soft_deleted_at IS NULL;
            """,
            
            # Index for gender-based searches
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patients_gender_active 
            ON patients (gender, active) 
            WHERE active = true AND soft_deleted_at IS NULL AND gender IS NOT NULL;
            """,
            
            # Partial index for IRIS sync status
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_patients_iris_sync 
            ON patients (iris_sync_status, iris_last_sync_at) 
            WHERE iris_sync_status IS NOT NULL;
            """
        ]
    
    @staticmethod
    def get_clinical_document_indexes() -> List[str]:
        """Get indexes for clinical document optimization."""
        return [
            # Patient document lookup
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_clinical_documents_patient 
            ON clinical_documents (patient_id, created_at DESC) 
            WHERE soft_deleted_at IS NULL;
            """,
            
            # Document type searches
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_clinical_documents_type 
            ON clinical_documents (document_type, created_at DESC) 
            WHERE soft_deleted_at IS NULL;
            """,
            
            # FHIR resource lookups
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_clinical_documents_fhir 
            ON clinical_documents (fhir_resource_type, fhir_resource_id) 
            WHERE fhir_resource_type IS NOT NULL AND fhir_resource_id IS NOT NULL;
            """
        ]
    
    @staticmethod
    def get_consent_indexes() -> List[str]:
        """Get indexes for consent management optimization."""
        return [
            # Patient consent lookups
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_consents_patient_status 
            ON consents (patient_id, status, effective_period_start DESC) 
            WHERE status = 'active';
            """,
            
            # Consent type searches
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_consents_types 
            ON consents USING gin (consent_types) 
            WHERE status = 'active';
            """,
            
            # Effective period queries
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_consents_effective_period 
            ON consents (effective_period_start, effective_period_end) 
            WHERE status = 'active';
            """
        ]
    
    async def apply_optimization_indexes(self, session: AsyncSession) -> Dict[str, bool]:
        """Apply database optimization indexes."""
        results = {}
        
        # Get all index creation statements
        all_indexes = (
            self.get_patient_lookup_indexes() + 
            self.get_clinical_document_indexes() + 
            self.get_consent_indexes()
        )
        
        for index_sql in all_indexes:
            try:
                # Extract index name for tracking
                index_name = index_sql.split("idx_")[1].split()[0] if "idx_" in index_sql else "unknown"
                
                await session.execute(text(index_sql))
                await session.commit()
                
                results[f"idx_{index_name}"] = True
                logger.info(f"Successfully created index: idx_{index_name}")
                
            except Exception as e:
                results[f"idx_{index_name}"] = False
                logger.error(f"Failed to create index: idx_{index_name}", error=str(e))
        
        return results


class DatabaseMaintenanceOptimizer:
    """Database maintenance and optimization procedures."""
    
    async def analyze_table_statistics(self, session: AsyncSession) -> Dict[str, Any]:
        """Analyze table statistics for optimization."""
        tables = ["patients", "clinical_documents", "consents", "immunizations"]
        statistics = {}
        
        for table in tables:
            try:
                # Get table statistics
                stats_query = text(f"""
                    SELECT 
                        schemaname,
                        tablename,
                        attname,
                        n_distinct,
                        correlation,
                        most_common_vals,
                        most_common_freqs
                    FROM pg_stats 
                    WHERE tablename = '{table}'
                    ORDER BY n_distinct DESC
                """)
                
                result = await session.execute(stats_query)
                table_stats = result.fetchall()
                
                statistics[table] = [dict(row._mapping) for row in table_stats]
                
            except Exception as e:
                logger.error(f"Failed to get statistics for table {table}", error=str(e))
                statistics[table] = []
        
        return statistics
    
    async def get_slow_queries(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """Get slow query statistics."""
        try:
            slow_query_sql = text("""
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows,
                    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                FROM pg_stat_statements 
                WHERE mean_time > 100  -- Queries taking more than 100ms on average
                ORDER BY mean_time DESC 
                LIMIT 10
            """)
            
            result = await session.execute(slow_query_sql)
            return [dict(row._mapping) for row in result.fetchall()]
            
        except Exception as e:
            logger.error("Failed to get slow query statistics", error=str(e))
            return []
    
    async def vacuum_analyze_tables(self, session: AsyncSession) -> Dict[str, bool]:
        """Perform VACUUM ANALYZE on key tables."""
        tables = ["patients", "clinical_documents", "consents", "immunizations"]
        results = {}
        
        for table in tables:
            try:
                # VACUUM ANALYZE to update statistics and reclaim space
                await session.execute(text(f"VACUUM ANALYZE {table}"))
                results[table] = True
                logger.info(f"Successfully vacuumed and analyzed table: {table}")
                
            except Exception as e:
                results[table] = False
                logger.error(f"Failed to vacuum analyze table {table}", error=str(e))
        
        return results


# =============================================================================
# OPTIMIZATION FACADE
# =============================================================================

class DatabaseOptimizationManager:
    """Main interface for database optimization features."""
    
    def __init__(self):
        self.db_optimizer = DatabaseOptimizer()
        self.patient_optimizer = PatientLookupOptimizer(self.db_optimizer)
        self.connection_optimizer = ConnectionPoolOptimizer()
        self.index_optimizer = QueryOptimizationIndexes()
        self.maintenance_optimizer = DatabaseMaintenanceOptimizer()
    
    async def optimize_patient_lookup(
        self,
        session: AsyncSession,
        lookup_type: str,
        lookup_value: str
    ) -> Optional[Patient]:
        """Optimized patient lookup with automatic method selection."""
        
        if lookup_type == "mrn":
            return await self.patient_optimizer.lookup_patient_by_mrn(lookup_value, session)
        elif lookup_type == "external_id":
            return await self.patient_optimizer.lookup_patient_by_external_id(lookup_value, session)
        else:
            raise ValueError(f"Unsupported lookup type: {lookup_type}")
    
    async def apply_all_optimizations(self, session: AsyncSession) -> Dict[str, Any]:
        """Apply all database optimizations."""
        results = {
            "indexes": await self.index_optimizer.apply_optimization_indexes(session),
            "maintenance": await self.maintenance_optimizer.vacuum_analyze_tables(session),
            "performance_metrics": len(self.db_optimizer.performance_metrics)
        }
        
        return results
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance optimization summary."""
        if not self.db_optimizer.performance_metrics:
            return {"message": "No performance metrics collected yet"}
        
        # Calculate performance statistics
        execution_times = [m.execution_time_ms for m in self.db_optimizer.performance_metrics]
        
        return {
            "total_queries": len(self.db_optimizer.performance_metrics),
            "avg_execution_time_ms": sum(execution_times) / len(execution_times),
            "max_execution_time_ms": max(execution_times),
            "min_execution_time_ms": min(execution_times),
            "cache_hit_rate": len([m for m in self.db_optimizer.performance_metrics if m.cache_hit]) / len(self.db_optimizer.performance_metrics) * 100,
            "slow_queries": len([m for m in self.db_optimizer.performance_metrics if m.execution_time_ms > 200])
        }


# Global optimization manager instance
optimization_manager = DatabaseOptimizationManager()