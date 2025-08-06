"""
Document History Tracker

Comprehensive history tracking for document versions with analytics and insights.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import structlog
from collections import defaultdict

logger = structlog.get_logger(__name__)

class VersionEventType(Enum):
    """Types of version events."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    RESTORED = "restored"
    ARCHIVED = "archived"
    ACCESSED = "accessed"
    DOWNLOADED = "downloaded"
    SHARED = "shared"

@dataclass
class VersionEvent:
    """Represents a single version event."""
    
    event_id: str
    document_id: str
    version_id: str
    event_type: VersionEventType
    timestamp: datetime
    user_id: str
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class VersionHistory:
    """Comprehensive version history for a document."""
    
    document_id: str
    total_versions: int
    first_version_date: datetime
    last_version_date: datetime
    total_events: int
    events: List[VersionEvent] = field(default_factory=list)
    analytics: Dict[str, Any] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)

class HistoryTracker:
    """Advanced document history tracking and analytics."""
    
    def __init__(self):
        self.events: List[VersionEvent] = []
        self.analytics_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_expiry: Dict[str, datetime] = {}
    
    def track_event(
        self,
        document_id: str,
        version_id: str,
        event_type: VersionEventType,
        user_id: str,
        details: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Track a version event.
        
        Args:
            document_id: Document identifier
            version_id: Version identifier
            event_type: Type of event
            user_id: User who triggered the event
            details: Event-specific details
            metadata: Additional metadata
            
        Returns:
            Event ID
        """
        
        import uuid
        
        event_id = str(uuid.uuid4())
        
        event = VersionEvent(
            event_id=event_id,
            document_id=document_id,
            version_id=version_id,
            event_type=event_type,
            timestamp=datetime.now(),
            user_id=user_id,
            details=details or {},
            metadata=metadata or {}
        )
        
        self.events.append(event)
        
        # Invalidate analytics cache for this document
        if document_id in self.analytics_cache:
            del self.analytics_cache[document_id]
            del self.cache_expiry[document_id]
        
        logger.info(
            "Version event tracked",
            event_id=event_id,
            document_id=document_id,
            version_id=version_id,
            event_type=event_type.value,
            user_id=user_id
        )
        
        return event_id
    
    def get_document_history(
        self,
        document_id: str,
        include_analytics: bool = True,
        include_insights: bool = True
    ) -> VersionHistory:
        """
        Get comprehensive history for a document.
        
        Args:
            document_id: Document identifier
            include_analytics: Whether to include analytics
            include_insights: Whether to include insights
            
        Returns:
            VersionHistory object
        """
        
        # Get events for this document
        document_events = [e for e in self.events if e.document_id == document_id]
        
        if not document_events:
            # Return empty history
            return VersionHistory(
                document_id=document_id,
                total_versions=0,
                first_version_date=datetime.now(),
                last_version_date=datetime.now(),
                total_events=0,
                events=[],
                analytics={},
                insights=[]
            )
        
        # Sort events by timestamp
        document_events.sort(key=lambda e: e.timestamp)
        
        # Get unique versions
        version_ids = list(set(e.version_id for e in document_events))
        
        # Calculate basic statistics
        first_version_date = document_events[0].timestamp
        last_version_date = document_events[-1].timestamp
        
        history = VersionHistory(
            document_id=document_id,
            total_versions=len(version_ids),
            first_version_date=first_version_date,
            last_version_date=last_version_date,
            total_events=len(document_events),
            events=document_events
        )
        
        # Add analytics if requested
        if include_analytics:
            history.analytics = self._generate_analytics(document_id, document_events)
        
        # Add insights if requested
        if include_insights:
            history.insights = self._generate_insights(document_id, document_events, history.analytics)
        
        logger.info(
            "Document history retrieved",
            document_id=document_id,
            total_versions=history.total_versions,
            total_events=history.total_events,
            timespan_days=(last_version_date - first_version_date).days
        )
        
        return history
    
    def get_user_activity(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get user activity statistics.
        
        Args:
            user_id: User identifier
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            User activity statistics
        """
        
        # Filter events by user and date range
        user_events = [e for e in self.events if e.user_id == user_id]
        
        if start_date:
            user_events = [e for e in user_events if e.timestamp >= start_date]
        
        if end_date:
            user_events = [e for e in user_events if e.timestamp <= end_date]
        
        if not user_events:
            return {
                "user_id": user_id,
                "total_events": 0,
                "event_types": {},
                "documents_touched": 0,
                "most_active_day": None,
                "activity_timeline": []
            }
        
        # Analyze activity
        event_types = defaultdict(int)
        documents = set()
        daily_activity = defaultdict(int)
        
        for event in user_events:
            event_types[event.event_type.value] += 1
            documents.add(event.document_id)
            day = event.timestamp.date()
            daily_activity[day] += 1
        
        # Find most active day
        most_active_day = max(daily_activity.items(), key=lambda x: x[1]) if daily_activity else None
        
        # Create activity timeline
        timeline = []
        for date, count in sorted(daily_activity.items()):
            timeline.append({
                "date": date.isoformat(),
                "event_count": count
            })
        
        activity = {
            "user_id": user_id,
            "total_events": len(user_events),
            "event_types": dict(event_types),
            "documents_touched": len(documents),
            "most_active_day": {
                "date": most_active_day[0].isoformat(),
                "event_count": most_active_day[1]
            } if most_active_day else None,
            "activity_timeline": timeline,
            "date_range": {
                "start": start_date.isoformat() if start_date else user_events[0].timestamp.date().isoformat(),
                "end": end_date.isoformat() if end_date else user_events[-1].timestamp.date().isoformat()
            }
        }
        
        logger.info(
            "User activity analyzed",
            user_id=user_id,
            total_events=activity["total_events"],
            documents_touched=activity["documents_touched"]
        )
        
        return activity
    
    def get_system_overview(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get system-wide document activity overview.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            System overview statistics
        """
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_events = [e for e in self.events if e.timestamp >= cutoff_date]
        
        if not recent_events:
            return {
                "period_days": days,
                "total_events": 0,
                "active_documents": 0,
                "active_users": 0,
                "event_types": {},
                "daily_activity": [],
                "top_documents": [],
                "top_users": []
            }
        
        # Analyze system activity
        event_types = defaultdict(int)
        documents = defaultdict(int)
        users = defaultdict(int)
        daily_activity = defaultdict(int)
        
        for event in recent_events:
            event_types[event.event_type.value] += 1
            documents[event.document_id] += 1
            users[event.user_id] += 1
            day = event.timestamp.date()
            daily_activity[day] += 1
        
        # Create daily activity timeline
        timeline = []
        for date, count in sorted(daily_activity.items()):
            timeline.append({
                "date": date.isoformat(),
                "event_count": count
            })
        
        # Get top documents and users
        top_documents = [
            {"document_id": doc_id, "event_count": count}
            for doc_id, count in sorted(documents.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        top_users = [
            {"user_id": user_id, "event_count": count}
            for user_id, count in sorted(users.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        overview = {
            "period_days": days,
            "total_events": len(recent_events),
            "active_documents": len(documents),
            "active_users": len(users),
            "event_types": dict(event_types),
            "daily_activity": timeline,
            "top_documents": top_documents,
            "top_users": top_users,
            "analysis_date": datetime.now().isoformat()
        }
        
        logger.info(
            "System overview generated",
            period_days=days,
            total_events=overview["total_events"],
            active_documents=overview["active_documents"],
            active_users=overview["active_users"]
        )
        
        return overview
    
    def _generate_analytics(self, document_id: str, events: List[VersionEvent]) -> Dict[str, Any]:
        """Generate analytics for document events."""
        
        # Check cache first
        if document_id in self.analytics_cache:
            cache_time = self.cache_expiry.get(document_id, datetime.min)
            if datetime.now() - cache_time < timedelta(minutes=10):  # 10-minute cache
                return self.analytics_cache[document_id]
        
        analytics = {}
        
        # Event type distribution
        event_types = defaultdict(int)
        for event in events:
            event_types[event.event_type.value] += 1
        analytics["event_types"] = dict(event_types)
        
        # User activity
        user_activity = defaultdict(int)
        for event in events:
            user_activity[event.user_id] += 1
        analytics["user_activity"] = dict(user_activity)
        analytics["most_active_user"] = max(user_activity.items(), key=lambda x: x[1]) if user_activity else None
        
        # Timeline analysis
        if len(events) > 1:
            first_event = events[0]
            last_event = events[-1]
            timespan = last_event.timestamp - first_event.timestamp
            
            analytics["timespan"] = {
                "total_days": timespan.days,
                "total_hours": timespan.total_seconds() / 3600,
                "first_event": first_event.timestamp.isoformat(),
                "last_event": last_event.timestamp.isoformat()
            }
            
            # Activity frequency
            if timespan.days > 0:
                analytics["activity_frequency"] = {
                    "events_per_day": len(events) / timespan.days,
                    "versions_per_week": len(set(e.version_id for e in events)) / max(timespan.days / 7, 1)
                }
        
        # Version statistics
        versions = list(set(e.version_id for e in events))
        analytics["versions"] = {
            "total_versions": len(versions),
            "creation_events": event_types.get("created", 0),
            "modification_events": event_types.get("modified", 0),
            "access_events": event_types.get("accessed", 0) + event_types.get("downloaded", 0)
        }
        
        # Recent activity (last 7 days)
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_events = [e for e in events if e.timestamp >= recent_cutoff]
        analytics["recent_activity"] = {
            "events_last_7_days": len(recent_events),
            "users_last_7_days": len(set(e.user_id for e in recent_events)),
            "most_recent_event": events[-1].timestamp.isoformat() if events else None
        }
        
        # Cache the results
        self.analytics_cache[document_id] = analytics
        self.cache_expiry[document_id] = datetime.now()
        
        return analytics
    
    def _generate_insights(
        self,
        document_id: str,
        events: List[VersionEvent],
        analytics: Dict[str, Any]
    ) -> List[str]:
        """Generate insights based on document history and analytics."""
        
        insights = []
        
        # Version activity insights
        total_versions = analytics["versions"]["total_versions"]
        if total_versions == 1:
            insights.append("This document has only one version - consider if updates are needed")
        elif total_versions > 10:
            insights.append(f"This document is highly active with {total_versions} versions")
        
        # User collaboration insights
        user_count = len(analytics["user_activity"])
        if user_count == 1:
            insights.append("This document is maintained by a single user")
        elif user_count > 5:
            insights.append(f"This document has high collaboration with {user_count} contributors")
        
        # Activity frequency insights
        if "activity_frequency" in analytics:
            events_per_day = analytics["activity_frequency"]["events_per_day"]
            if events_per_day > 2:
                insights.append("This document has high daily activity - consider workflow optimization")
            elif events_per_day < 0.1:
                insights.append("This document has low activity - consider archival or review")
        
        # Recent activity insights
        recent_events = analytics["recent_activity"]["events_last_7_days"]
        if recent_events == 0:
            insights.append("No recent activity in the last 7 days")
        elif recent_events > 10:
            insights.append("High activity in the last 7 days - document may be in active development")
        
        # Event pattern insights
        event_types = analytics["event_types"]
        access_events = event_types.get("accessed", 0) + event_types.get("downloaded", 0)
        modification_events = event_types.get("modified", 0) + event_types.get("created", 0)
        
        if access_events > modification_events * 5:
            insights.append("Document is frequently accessed but rarely modified - consider read-only optimization")
        elif modification_events > access_events:
            insights.append("Document is modified more than accessed - consider review workflow")
        
        # Time-based insights
        if "timespan" in analytics:
            total_days = analytics["timespan"]["total_days"]
            if total_days > 365:
                insights.append("Long-lived document with over a year of history")
            elif total_days < 1:
                insights.append("Recently created document")
        
        # User dominance insights
        if analytics.get("most_active_user"):
            most_active_user, activity_count = analytics["most_active_user"]
            total_events = len(events)
            dominance_ratio = activity_count / total_events
            
            if dominance_ratio > 0.8:
                insights.append(f"Document activity is dominated by one user ({dominance_ratio:.0%})")
            elif dominance_ratio < 0.3 and user_count > 2:
                insights.append("Document has well-distributed collaborative activity")
        
        return insights
    
    def clear_cache(self):
        """Clear analytics cache."""
        self.analytics_cache.clear()
        self.cache_expiry.clear()
        logger.info("Analytics cache cleared")
    
    def get_events_by_type(
        self,
        event_type: VersionEventType,
        document_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[VersionEvent]:
        """Get events filtered by type and optional document/user."""
        
        filtered_events = [e for e in self.events if e.event_type == event_type]
        
        if document_id:
            filtered_events = [e for e in filtered_events if e.document_id == document_id]
        
        if user_id:
            filtered_events = [e for e in filtered_events if e.user_id == user_id]
        
        return filtered_events