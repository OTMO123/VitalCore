"""
Enhanced Audit Service for SOC2 Type 2 Compliance
Provides comprehensive activity logging and monitoring
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
import structlog

from app.core.database_unified import AuditLog, AuditEventType, User
from app.core.security import get_client_info

logger = structlog.get_logger()

class EnhancedAuditService:
    """Enhanced audit service with SOC2 Type 2 compliance features."""
    
    # ============================================
    # ACTIVITY CATEGORIZATION FOR SOC2
    # ============================================
    
    ACTIVITY_CATEGORIES = {
        # Security Events (CRITICAL)
        'security': [
            'user_login_failed', 'user_locked', 'security_violation', 
            'unauthorized_access', 'suspicious_activity', 'data_breach_detected'
        ],
        
        # PHI Access Events (CRITICAL for HIPAA)
        'phi': [
            'phi_accessed', 'phi_created', 'phi_updated', 'phi_deleted', 
            'phi_exported', 'patient_accessed', 'patient_search'
        ],
        
        # Administrative Actions
        'admin': [
            'user_created', 'user_updated', 'user_deleted', 'role_changed',
            'permission_granted', 'config_changed', 'security_policy_updated'
        ],
        
        # System Events
        'system': [
            'system_error', 'database_error', 'performance_issue',
            'iris_sync_completed', 'iris_sync_failed', 'external_api_error'
        ],
        
        # Compliance Events
        'compliance': [
            'consent_granted', 'consent_withdrawn', 'consent_updated',
            'audit_report_generated', 'data_retention_applied'
        ]
    }
    
    SEVERITY_MAPPING = {
        # Critical - Immediate attention required
        'critical': [
            'data_breach_detected', 'unauthorized_access', 'phi_deleted',
            'security_violation', 'system_error'
        ],
        
        # High - Security/compliance concern
        'high': [
            'user_login_failed', 'suspicious_activity', 'phi_exported',
            'config_changed', 'user_deleted', 'consent_withdrawn'
        ],
        
        # Medium - Important operational events
        'medium': [
            'phi_accessed', 'patient_accessed', 'user_created',
            'role_changed', 'iris_sync_failed'
        ],
        
        # Low - Routine operations
        'low': [
            'user_login', 'user_logout', 'patient_created',
            'iris_sync_completed', 'consent_granted'
        ]
    }
    
    async def get_enhanced_activities(
        self, 
        db: AsyncSession,
        limit: int = 50,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        hours: int = 24,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get enhanced activity logs with SOC2 compliance metadata.
        
        Args:
            db: Database session
            limit: Maximum number of activities to return
            category: Filter by category (security, phi, admin, system, compliance)
            severity: Filter by severity (critical, high, medium, low)
            hours: Time range in hours
            user_id: Filter by specific user
        
        Returns:
            List of enhanced activity items
        """
        try:
            # Build query conditions
            conditions = [
                AuditLog.timestamp >= datetime.utcnow() - timedelta(hours=hours)
            ]
            
            if user_id:
                conditions.append(AuditLog.user_id == user_id)
            
            # Filter by category
            if category and category in self.ACTIVITY_CATEGORIES:
                event_types = self.ACTIVITY_CATEGORIES[category]
                conditions.append(AuditLog.event_type.in_(event_types))
            
            # Execute query
            query = (
                select(AuditLog, User.username, User.email)
                .outerjoin(User, AuditLog.user_id == User.id)
                .where(and_(*conditions))
                .order_by(desc(AuditLog.timestamp))
                .limit(limit)
            )
            
            result = await db.execute(query)
            audit_logs = result.fetchall()
            
            # Transform to enhanced format
            enhanced_activities = []
            for audit_log, username, email in audit_logs:
                activity = await self._transform_to_enhanced_activity(
                    audit_log, username, email
                )
                
                # Apply severity filter
                if severity and activity.get('severity') != severity:
                    continue
                    
                enhanced_activities.append(activity)
            
            # Return real data only - no mock data fallback
            if not enhanced_activities:
                logger.info("No real audit data found in specified time range", 
                          category=category, severity=severity, hours=hours)
            
            logger.info(
                "Enhanced activities retrieved",
                count=len(enhanced_activities),
                category=category,
                severity=severity,
                hours=hours,
                is_mock_data=len(enhanced_activities) > 0 and not audit_logs
            )
            
            return enhanced_activities
            
        except Exception as e:
            logger.error("Failed to get enhanced activities", error=str(e))
            # Return empty list on error
            return []
    
    async def _transform_to_enhanced_activity(
        self,
        audit_log: AuditLog,
        username: Optional[str],
        email: Optional[str]
    ) -> Dict[str, Any]:
        """Transform audit log to enhanced activity format."""
        
        # Convert enum to string safely
        event_type = str(audit_log.event_type.value) if hasattr(audit_log.event_type, 'value') else str(audit_log.event_type)
        event_type_lower = event_type.lower()
        
        category = self._get_activity_category(event_type_lower)
        severity = self._get_activity_severity(event_type_lower)
        
        # Generate human-readable title and description
        title, description = self._generate_activity_text(audit_log, username)
        
        # Extract compliance flags
        compliance_flags = self._extract_compliance_flags(audit_log)
        
        return {
            'id': str(audit_log.id),
            'type': event_type_lower,
            'category': category,
            'title': title,
            'description': description,
            'timestamp': audit_log.timestamp.isoformat(),
            'user': username or 'System',
            'userId': str(audit_log.user_id) if audit_log.user_id else None,
            'severity': severity,
            'ipAddress': audit_log.ip_address,
            'userAgent': audit_log.user_agent,
            'resourceId': str(audit_log.resource_id) if audit_log.resource_id else None,
            'resourceType': audit_log.resource_type,
            'metadata': audit_log.config_metadata or {},
            'complianceFlags': compliance_flags,
            'result': audit_log.outcome,
            'action': audit_log.action,
        }
    
    def _get_activity_category(self, event_type: str) -> str:
        """Determine activity category from event type."""
        for category, types in self.ACTIVITY_CATEGORIES.items():
            if event_type in types:
                return category
        return 'system'  # Default category
    
    def _get_activity_severity(self, event_type: str) -> str:
        """Determine activity severity from event type."""
        for severity, types in self.SEVERITY_MAPPING.items():
            if event_type in types:
                return severity
        return 'info'  # Default severity
    
    def _generate_activity_text(
        self, 
        audit_log: AuditLog, 
        username: Optional[str]
    ) -> tuple[str, str]:
        """Generate human-readable title and description."""
        
        # Convert enum to string safely
        event_type = str(audit_log.event_type.value) if hasattr(audit_log.event_type, 'value') else str(audit_log.event_type)
        event_type_lower = event_type.lower()
        
        user = username or 'System User'
        metadata = audit_log.config_metadata or {}
        
        # Event-specific text generation
        if event_type_lower == 'user_login':
            title = f"User Login"
            description = f"{user} successfully logged into the system"
            
        elif event_type_lower == 'user_login_failed':
            title = f"Failed Login Attempt"
            description = f"Failed login attempt for user {user}"
            
        elif event_type_lower == 'phi_accessed':
            patient_id = metadata.get('patient_id', 'Unknown')
            title = f"PHI Access"
            description = f"{user} accessed protected health information for patient {patient_id}"
            
        elif event_type_lower == 'phi_exported':
            title = f"PHI Data Export"
            description = f"{user} exported protected health information - HIPAA audit required"
            
        elif event_type_lower == 'user_created':
            created_user = metadata.get('created_username', 'Unknown')
            title = f"User Account Created"
            description = f"{user} created new user account: {created_user}"
            
        elif event_type_lower == 'config_changed':
            setting = metadata.get('setting_name', 'system setting')
            title = f"Configuration Changed"
            description = f"{user} modified {setting}"
            
        elif event_type_lower == 'security_violation':
            violation_type = metadata.get('violation_type', 'unknown')
            title = f"Security Violation Detected"
            description = f"Security violation detected: {violation_type} by {user}"
            
        elif event_type_lower == 'consent_withdrawn':
            patient_id = metadata.get('patient_id', 'Unknown')
            title = f"Patient Consent Withdrawn"
            description = f"Patient {patient_id} withdrew consent for data processing"
            
        elif event_type_lower == 'iris_sync_completed':
            records_count = metadata.get('records_synced', 0)
            title = f"IRIS Sync Completed"
            description = f"Successfully synced {records_count} records with IRIS system"
            
        elif event_type_lower == 'iris_sync_failed':
            error = metadata.get('error', 'Unknown error')
            title = f"IRIS Sync Failed"
            description = f"IRIS synchronization failed: {error}"
            
        else:
            # Generic format for unknown events
            title = f"{event_type_lower.replace('_', ' ').title()}"
            description = f"{user} performed {audit_log.action} on {audit_log.resource_type or 'system'}"
        
        return title, description
    
    def _extract_compliance_flags(self, audit_log: AuditLog) -> List[str]:
        """Extract compliance-related flags from audit log."""
        flags = []
        
        # Add compliance tags from the log
        if audit_log.compliance_tags:
            flags.extend(audit_log.compliance_tags)
        
        # Add event-specific compliance flags
        # Convert enum to string safely
        event_type = str(audit_log.event_type.value) if hasattr(audit_log.event_type, 'value') else str(audit_log.event_type)
        event_type_lower = event_type.lower()
        
        if event_type_lower.startswith('phi_'):
            flags.append('HIPAA')
        
        if event_type_lower in ['user_login_failed', 'security_violation']:
            flags.append('SOC2-Security')
        
        if event_type_lower in ['config_changed', 'user_created', 'user_deleted']:
            flags.append('SOC2-Availability')
        
        if event_type_lower.startswith('consent_'):
            flags.extend(['HIPAA', 'GDPR'])
        
        return list(set(flags))  # Remove duplicates
    
    async def get_security_summary(self, db: AsyncSession, hours: int = 24) -> Dict[str, Any]:
        """Get security summary for dashboard."""
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            
            # Count events by category
            query = (
                select(
                    AuditLog.event_type,
                    func.count(AuditLog.id).label('count')
                )
                .where(AuditLog.timestamp >= since)
                .group_by(AuditLog.event_type)
            )
            
            result = await db.execute(query)
            event_counts = {row[0]: row[1] for row in result.fetchall()}
            
            # Categorize counts
            summary = {
                'total_events': sum(event_counts.values()),
                'security_events': 0,
                'phi_events': 0,
                'critical_events': 0,
                'failed_logins': event_counts.get('user_login_failed', 0),
                'phi_access_count': event_counts.get('phi_accessed', 0),
                'admin_actions': 0,
                'time_range_hours': hours,
            }
            
            # Calculate category totals
            for event_type, count in event_counts.items():
                category = self._get_activity_category(event_type)
                severity = self._get_activity_severity(event_type)
                
                if category == 'security':
                    summary['security_events'] += count
                elif category == 'phi':
                    summary['phi_events'] += count
                elif category == 'admin':
                    summary['admin_actions'] += count
                
                if severity in ['critical', 'high']:
                    summary['critical_events'] += count
            
            # Keep real data only - no mock fallback
            
            return summary
            
        except Exception as e:
            logger.error("Failed to get security summary", error=str(e))
            # Return empty summary on error
            return {
                'total_events': 0,
                'security_events': 0,
                'phi_events': 0,
                'critical_events': 0,
                'failed_logins': 0,
                'phi_access_count': 0,
                'admin_actions': 0,
                'time_range_hours': hours,
            }

# Global service instance
enhanced_audit_service = EnhancedAuditService()