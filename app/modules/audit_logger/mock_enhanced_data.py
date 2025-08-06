"""
Mock Enhanced Audit Data for SOC2 Demonstration
Генерирует реалистичные данные для демонстрации SOC2-совместимого логирования
"""

from datetime import datetime, timedelta
import random
import uuid
from typing import List, Dict, Any

def generate_mock_enhanced_activities(limit: int = 20) -> List[Dict[str, Any]]:
    """Generate realistic mock enhanced activity data for SOC2 dashboard."""
    
    activities = []
    now = datetime.utcnow()
    
    # Mock users
    users = [
        {"name": "admin", "id": "c4c4fec4-c63a-49d1-a5c7-07495c4740b0"},
        {"name": "dr.smith", "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"},
        {"name": "nurse.johnson", "id": "b2c3d4e5-f6g7-8901-bcde-f23456789012"},
        {"name": "system", "id": "00000000-0000-0000-0000-000000000000"},
        {"name": "receptionist", "id": "c3d4e5f6-g7h8-9012-cdef-345678901234"},
    ]
    
    # Mock IPs
    ips = ["192.168.1.100", "10.0.0.50", "172.16.0.25", "127.0.0.1", "192.168.1.200"]
    
    # Mock activity templates
    activity_templates = [
        # Security Events (CRITICAL)
        {
            "type": "user_login_failed",
            "category": "security",
            "severity": "high",
            "title": "Failed Login Attempt",
            "description": "Failed login attempt for user {user}",
            "complianceFlags": ["SOC2-Security", "Authentication"]
        },
        {
            "type": "security_violation",
            "category": "security", 
            "severity": "critical",
            "title": "Security Violation Detected",
            "description": "Multiple failed login attempts detected from IP {ip}",
            "complianceFlags": ["SOC2-Security", "Incident"]
        },
        {
            "type": "unauthorized_access",
            "category": "security",
            "severity": "critical", 
            "title": "Unauthorized Access Attempt",
            "description": "Attempt to access restricted resource without proper authorization",
            "complianceFlags": ["SOC2-Security", "Access-Control"]
        },
        
        # PHI Access Events (CRITICAL for HIPAA)
        {
            "type": "phi_accessed",
            "category": "phi",
            "severity": "medium",
            "title": "PHI Access",
            "description": "{user} accessed protected health information for patient P-{patient_id}",
            "complianceFlags": ["HIPAA", "PHI-Access"]
        },
        {
            "type": "phi_exported",
            "category": "phi",
            "severity": "high",
            "title": "PHI Data Export",
            "description": "{user} exported PHI data - HIPAA audit required",
            "complianceFlags": ["HIPAA", "Data-Export", "SOC2-Confidentiality"]
        },
        {
            "type": "patient_accessed",
            "category": "phi",
            "severity": "medium",
            "title": "Patient Record Access",
            "description": "{user} viewed patient record for P-{patient_id}",
            "complianceFlags": ["HIPAA", "Patient-Access"]
        },
        
        # Administrative Actions
        {
            "type": "user_created",
            "category": "admin",
            "severity": "medium",
            "title": "User Account Created",
            "description": "{user} created new user account: {new_user}",
            "complianceFlags": ["SOC2-Availability", "User-Management"]
        },
        {
            "type": "role_changed",
            "category": "admin",
            "severity": "high",
            "title": "User Role Modified",
            "description": "{user} changed user role for {target_user}",
            "complianceFlags": ["SOC2-Security", "Role-Management"]
        },
        {
            "type": "config_changed",
            "category": "admin",
            "severity": "high",
            "title": "System Configuration Changed",
            "description": "{user} modified security policy settings",
            "complianceFlags": ["SOC2-Security", "Configuration"]
        },
        
        # System Events
        {
            "type": "iris_sync_completed",
            "category": "system",
            "severity": "low",
            "title": "IRIS Sync Completed",
            "description": "Successfully synced {count} records with IRIS system",
            "complianceFlags": ["SOC2-Processing"]
        },
        {
            "type": "iris_sync_failed",
            "category": "system",
            "severity": "medium",
            "title": "IRIS Sync Failed", 
            "description": "IRIS synchronization failed: Connection timeout",
            "complianceFlags": ["SOC2-Availability", "Integration"]
        },
        {
            "type": "database_error",
            "category": "system",
            "severity": "critical",
            "title": "Database Error",
            "description": "Database connection pool exhausted - performance degraded",
            "complianceFlags": ["SOC2-Availability"]
        },
        
        # Compliance Events
        {
            "type": "consent_granted",
            "category": "compliance",
            "severity": "low",
            "title": "Patient Consent Granted",
            "description": "Patient P-{patient_id} granted consent for data processing",
            "complianceFlags": ["HIPAA", "GDPR", "Consent"]
        },
        {
            "type": "consent_withdrawn",
            "category": "compliance",
            "severity": "high",
            "title": "Patient Consent Withdrawn",
            "description": "Patient P-{patient_id} withdrew consent - data access restricted",
            "complianceFlags": ["HIPAA", "GDPR", "Consent"]
        },
        {
            "type": "audit_report_generated",
            "category": "compliance",
            "severity": "low",
            "title": "Compliance Report Generated",
            "description": "SOC2 Type II compliance report generated for audit period",
            "complianceFlags": ["SOC2", "Audit"]
        },
        
        # Recent login events (successful)
        {
            "type": "user_login",
            "category": "security",
            "severity": "low",
            "title": "User Login",
            "description": "{user} successfully logged into the system",
            "complianceFlags": ["Authentication"]
        }
    ]
    
    # Generate activities
    for i in range(limit):
        template = random.choice(activity_templates)
        user = random.choice(users)
        ip = random.choice(ips)
        
        # Generate timestamp (last 24 hours, weighted towards recent)
        hours_ago = random.expovariate(1/6)  # Most recent events more likely
        if hours_ago > 24:
            hours_ago = 24
        timestamp = now - timedelta(hours=hours_ago)
        
        # Fill in template
        activity = {
            "id": str(uuid.uuid4()),
            "type": template["type"],
            "category": template["category"],
            "title": template["title"],
            "description": template["description"].format(
                user=user["name"],
                ip=ip,
                patient_id=str(random.randint(1000, 9999)),
                new_user=f"newuser{random.randint(1, 100)}",
                target_user=random.choice(users)["name"],
                count=random.randint(10, 500)
            ),
            "timestamp": timestamp.isoformat(),
            "user": user["name"],
            "userId": user["id"],
            "severity": template["severity"],
            "ipAddress": ip,
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "resourceId": str(uuid.uuid4()) if template["category"] == "phi" else None,
            "resourceType": "patient_record" if template["category"] == "phi" else template["category"],
            "metadata": {
                "session_id": str(uuid.uuid4())[:8],
                "request_id": str(uuid.uuid4())[:8],
                "processing_time_ms": random.randint(50, 500),
                "compliance_level": "SOC2_Type_II",
            },
            "complianceFlags": template["complianceFlags"]
        }
        
        # Add category-specific metadata
        if template["category"] == "phi":
            activity["metadata"]["patient_id"] = f"P-{random.randint(1000, 9999)}"
            activity["metadata"]["data_sensitivity"] = "PHI"
            
        elif template["category"] == "security":
            activity["metadata"]["security_context"] = "authentication"
            activity["metadata"]["threat_level"] = template["severity"]
            
        elif template["category"] == "admin":
            activity["metadata"]["admin_action"] = template["type"]
            activity["metadata"]["requires_approval"] = template["severity"] in ["high", "critical"]
        
        activities.append(activity)
    
    # Sort by timestamp (most recent first)
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return activities

def generate_mock_security_summary() -> Dict[str, Any]:
    """Generate mock security summary data."""
    
    # Generate realistic numbers
    total_events = random.randint(150, 300)
    security_events = random.randint(5, 25)
    phi_events = random.randint(20, 60)
    critical_events = random.randint(0, 3)
    failed_logins = random.randint(0, 8)
    phi_access_count = random.randint(15, 45)
    admin_actions = random.randint(5, 15)
    
    return {
        "total_events": total_events,
        "security_events": security_events,
        "phi_events": phi_events,
        "critical_events": critical_events,
        "failed_logins": failed_logins,
        "phi_access_count": phi_access_count,
        "admin_actions": admin_actions,
        "time_range_hours": 24,
    }