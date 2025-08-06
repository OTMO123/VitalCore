"""
Dashboard API Router

Optimized endpoints for dashboard performance with bulk data fetching,
caching, and minimal API calls.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime
import structlog

from app.core.database_unified import get_db
from app.core.security import get_current_user_id, require_role
from app.modules.dashboard.service import get_dashboard_service
from app.modules.dashboard.schemas import (
    BulkDashboardResponse, BulkRefreshRequest, DashboardStats, 
    DashboardActivities, DashboardAlerts, DashboardHealth, PerformanceMetrics
)
from app.core.soc2_circuit_breaker import soc2_breaker_registry

logger = structlog.get_logger()

router = APIRouter()

# ============================================
# BULK DASHBOARD ENDPOINTS
# ============================================

@router.post("/refresh", response_model=BulkDashboardResponse)
async def bulk_dashboard_refresh(
    request: BulkRefreshRequest,
    current_user_id: str = Depends(get_current_user_id),
    _: dict = Depends(require_role("user")),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all dashboard data in a single optimized API call with authentication.
    
    This endpoint aggregates data from multiple services to minimize
    frontend API calls and improve dashboard performance.
    """
    try:
        dashboard_service = get_dashboard_service()
        
        # Initialize service if needed
        if not hasattr(dashboard_service, 'redis_client'):
            await dashboard_service.initialize()
        
        result = await dashboard_service.get_bulk_dashboard_data(request, db)
        
        logger.info("Dashboard bulk refresh completed",
                   user_id=current_user_id,
                   include_stats=request.include_stats,
                   include_activities=request.include_activities,
                   include_alerts=request.include_alerts,
                   generation_time_ms=result.metadata.get("generation_time_ms"))
        
        return result
        
    except Exception as e:
        logger.error("Dashboard bulk refresh failed", error=str(e))
        raise HTTPException(status_code=500, detail="Dashboard refresh failed")

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user_id: str = Depends(get_current_user_id),
    _: dict = Depends(require_role("user")),
    db: AsyncSession = Depends(get_db)
):
    """Get core dashboard statistics with authentication."""
    try:
        dashboard_service = get_dashboard_service()
        
        if not hasattr(dashboard_service, 'redis_client'):
            await dashboard_service.initialize()
        
        result = await dashboard_service._get_dashboard_stats(db)
        
        logger.info("Dashboard stats retrieved", user_id=current_user_id)
        return result
        
    except Exception as e:
        logger.error("Failed to get dashboard stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get dashboard statistics")

@router.get("/activities", response_model=DashboardActivities)
async def get_dashboard_activities(
    limit: int = Query(default=50, ge=1, le=200, description="Number of activities to return"),
    categories: Optional[str] = Query(default=None, description="Comma-separated list of categories"),
    time_range_hours: int = Query(default=24, ge=1, le=168, description="Time range in hours"),
    current_user_id: str = Depends(get_current_user_id),
    _: dict = Depends(require_role("user")),
    db: AsyncSession = Depends(get_db)
):
    """Get recent dashboard activities with authentication."""
    try:
        dashboard_service = get_dashboard_service()
        
        if not hasattr(dashboard_service, 'redis_client'):
            await dashboard_service.initialize()
        
        # Parse categories
        category_list = None
        if categories:
            category_list = [cat.strip() for cat in categories.split(',')]
        
        result = await dashboard_service._get_dashboard_activities(
            db, limit, category_list, time_range_hours
        )
        
        logger.info("Dashboard activities retrieved", 
                   user_id=current_user_id,
                   count=len(result.activities),
                   categories=category_list)
        return result
        
    except Exception as e:
        logger.error("Failed to get dashboard activities", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get dashboard activities")

@router.get("/alerts", response_model=DashboardAlerts)
async def get_dashboard_alerts(
    time_range_hours: int = Query(default=24, ge=1, le=168, description="Time range in hours"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard alerts."""
    try:
        dashboard_service = get_dashboard_service()
        
        if not hasattr(dashboard_service, 'redis_client'):
            await dashboard_service.initialize()
        
        result = await dashboard_service._get_dashboard_alerts(db, time_range_hours)
        
        logger.info("Dashboard alerts retrieved", 
                   user_id=current_user_id,
                   alert_count=len(result.alerts),
                   critical_count=result.critical_count)
        return result
        
    except Exception as e:
        logger.error("Failed to get dashboard alerts", 
                    user_id=current_user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get dashboard alerts")

# ============================================
# PERFORMANCE & HEALTH ENDPOINTS
# ============================================

@router.get("/health", response_model=DashboardHealth)
async def get_dashboard_health(
    current_user_id: str = Depends(get_current_user_id)
):
    """Get dashboard service health and performance metrics."""
    try:
        dashboard_service = get_dashboard_service()
        
        if not hasattr(dashboard_service, 'redis_client'):
            await dashboard_service.initialize()
        
        result = await dashboard_service.get_dashboard_health()
        
        logger.info("Dashboard health check completed", 
                   user_id=current_user_id,
                   status=result.status)
        return result
        
    except Exception as e:
        logger.error("Dashboard health check failed", 
                    user_id=current_user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Dashboard health check failed")

@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    current_user_id: str = Depends(get_current_user_id),
    _: dict = Depends(require_role("admin"))
):
    """Get dashboard performance metrics (admin only)."""
    try:
        dashboard_service = get_dashboard_service()
        
        if not hasattr(dashboard_service, 'redis_client'):
            await dashboard_service.initialize()
        
        result = await dashboard_service.get_performance_metrics()
        
        logger.info("Dashboard performance metrics retrieved", 
                   user_id=current_user_id)
        return result
        
    except Exception as e:
        logger.error("Failed to get performance metrics", 
                    user_id=current_user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")

# ============================================
# CACHE MANAGEMENT ENDPOINTS
# ============================================

@router.post("/cache/clear")
async def clear_dashboard_cache(
    current_user_id: str = Depends(get_current_user_id),
    _: dict = Depends(require_role("admin"))
):
    """Clear dashboard cache (admin only)."""
    try:
        dashboard_service = get_dashboard_service()
        
        if dashboard_service.redis_client:
            # Clear all dashboard cache keys
            keys = await dashboard_service.redis_client.keys(f"{dashboard_service.cache_prefix}:*")
            if keys:
                await dashboard_service.redis_client.delete(*keys)
                cleared_count = len(keys)
            else:
                cleared_count = 0
        else:
            cleared_count = 0
        
        logger.info("Dashboard cache cleared", 
                   user_id=current_user_id,
                   keys_cleared=cleared_count)
        
        return {
            "message": "Dashboard cache cleared successfully",
            "keys_cleared": cleared_count
        }
        
    except Exception as e:
        logger.error("Failed to clear dashboard cache", 
                    user_id=current_user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to clear cache")

@router.get("/cache/stats")
async def get_cache_stats(
    current_user_id: str = Depends(get_current_user_id),
    _: dict = Depends(require_role("admin"))
):
    """Get dashboard cache statistics (admin only)."""
    try:
        dashboard_service = get_dashboard_service()
        
        cache_stats = {
            "cache_enabled": dashboard_service.redis_client is not None,
            "cache_hits": dashboard_service.metrics["cache_hits"],
            "cache_misses": dashboard_service.metrics["cache_misses"],
            "total_requests": dashboard_service.metrics["requests_count"],
            "hit_rate_percentage": 0.0
        }
        
        if cache_stats["total_requests"] > 0:
            cache_stats["hit_rate_percentage"] = (
                cache_stats["cache_hits"] / cache_stats["total_requests"] * 100
            )
        
        if dashboard_service.redis_client:
            try:
                # Get Redis info
                redis_info = await dashboard_service.redis_client.info("memory")
                cache_stats["redis_memory_mb"] = round(redis_info["used_memory"] / 1024 / 1024, 2)
                cache_stats["redis_connected"] = True
            except Exception:
                cache_stats["redis_connected"] = False
        else:
            cache_stats["redis_connected"] = False
        
        logger.info("Dashboard cache stats retrieved", 
                   user_id=current_user_id)
        return cache_stats
        
    except Exception as e:
        logger.error("Failed to get cache stats", 
                    user_id=current_user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get cache statistics")

# ============================================
# SOC2 MONITORING ENDPOINTS
# ============================================

@router.get("/soc2/availability", response_model=dict)
async def get_soc2_availability_report(
    current_user_id: str = Depends(get_current_user_id),
    _: dict = Depends(require_role("admin"))
):
    """Get SOC2 Type 2 availability report for all dashboard components (admin only)."""
    try:
        dashboard_service = get_dashboard_service()
        
        if not hasattr(dashboard_service, 'redis_client'):
            await dashboard_service.initialize()
        
        # Get comprehensive SOC2 availability report
        soc2_report = await dashboard_service.get_soc2_availability_report()
        
        logger.info("SOC2 availability report retrieved", 
                   user_id=current_user_id,
                   overall_availability=soc2_report.get("overall_availability"),
                   critical_availability=soc2_report.get("critical_component_availability"),
                   compliance_status=soc2_report.get("soc2_compliance_status"))
        
        return soc2_report
        
    except Exception as e:
        logger.error("Failed to get SOC2 availability report", 
                    user_id=current_user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get SOC2 availability report")

@router.get("/soc2/circuit-breakers", response_model=dict)
async def get_circuit_breaker_status(
    current_user_id: str = Depends(get_current_user_id),
    _: dict = Depends(require_role("admin"))
):
    """Get current status of all SOC2 circuit breakers (admin only)."""
    try:
        # Get circuit breaker status from registry
        breaker_report = soc2_breaker_registry.get_soc2_availability_report()
        
        # Add real-time circuit breaker states
        current_states = {}
        for component_name, breaker in soc2_breaker_registry._breakers.items():
            metrics = breaker.get_soc2_metrics()
            current_states[component_name] = {
                "state": metrics.current_state.value,
                "failure_count": breaker.failure_count,
                "last_failure": metrics.last_failure_time.isoformat() if metrics.last_failure_time else None,
                "uptime_percentage": metrics.uptime_percentage,
                "is_critical": component_name in soc2_breaker_registry._critical_components
            }
        
        logger.info("SOC2 circuit breaker status retrieved",
                   user_id=current_user_id,
                   total_breakers=len(current_states),
                   critical_breakers=len(soc2_breaker_registry._critical_components))
        
        return {
            "circuit_breaker_states": current_states,
            "availability_summary": breaker_report,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get circuit breaker status",
                    user_id=current_user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get circuit breaker status")

@router.post("/soc2/circuit-breakers/{component_name}/reset")
async def reset_circuit_breaker(
    component_name: str,
    current_user_id: str = Depends(get_current_user_id),
    _: dict = Depends(require_role("admin"))
):
    """Manually reset a circuit breaker (admin only) - SOC2 incident response."""
    try:
        breaker = soc2_breaker_registry.get_breaker(component_name)
        
        if not breaker:
            raise HTTPException(status_code=404, detail=f"Circuit breaker '{component_name}' not found")
        
        # Log the manual reset for SOC2 audit trail
        logger.warning("SOC2 Manual Circuit Breaker Reset Initiated",
                      component=component_name,
                      admin_user=current_user_id,
                      previous_state=breaker.state.value,
                      soc2_control="CC8.1",  # SOC2 Change Management
                      incident_response=True)
        
        # Reset the circuit breaker
        breaker.reset()
        
        return {
            "message": f"Circuit breaker '{component_name}' reset successfully",
            "component": component_name,
            "new_state": breaker.state.value,
            "reset_by": current_user_id,
            "reset_timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to reset circuit breaker",
                    component=component_name,
                    user_id=current_user_id, 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to reset circuit breaker")

# ============================================
# PRODUCTION-READY ENDPOINTS ONLY
# All temporary test endpoints have been removed for security
# ============================================