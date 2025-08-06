import asyncio
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import structlog
import json
from uuid import uuid4

logger = structlog.get_logger()

class EventType(Enum):
    """Enumeration of system events for SOC2 compliance tracking."""
    
    # Authentication events
    USER_LOGIN_SUCCESS = "user.login.success"
    USER_LOGIN_FAILURE = "user.login.failure"
    USER_LOGOUT = "user.logout"
    TOKEN_CREATED = "token.created"
    TOKEN_EXPIRED = "token.expired"
    
    # Authorization events
    ACCESS_GRANTED = "access.granted"
    ACCESS_DENIED = "access.denied"
    PERMISSION_CHECK = "permission.check"
    
    # IRIS API events
    IRIS_API_REQUEST = "iris.api.request"
    IRIS_API_RESPONSE = "iris.api.response"
    IRIS_API_ERROR = "iris.api.error"
    IRIS_API_RETRY = "iris.api.retry"
    
    # Data events
    DATA_CREATED = "data.created"
    DATA_UPDATED = "data.updated"
    DATA_DELETED = "data.deleted"
    DATA_ACCESSED = "data.accessed"
    
    # Purge events
    PURGE_SCHEDULED = "purge.scheduled"
    PURGE_EXECUTED = "purge.executed"
    PURGE_SUSPENDED = "purge.suspended"
    PURGE_OVERRIDE = "purge.override"
    
    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    ERROR_OCCURRED = "error.occurred"
    SECURITY_VIOLATION = "security.violation"

@dataclass
class Event:
    """Event data structure for the event bus."""
    
    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: EventType = EventType.SYSTEM_STARTUP
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Core event data
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    
    # Event details
    action: str = ""
    outcome: str = "success"  # success, failure, error
    
    # Additional context
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Client information
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "outcome": self.outcome,
            "data": self.data,
            "metadata": self.metadata,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent
        }
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict(), default=str)

EventHandler = Callable[[Event], Any]

class EventBus:
    """Async event bus for decoupled module communication."""
    
    def __init__(self):
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._running = False
        self._event_queue: asyncio.Queue[Event] = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._stats = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0
        }
    
    async def start(self):
        """Start the event bus worker."""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._process_events())
        logger.info("Event bus started")
        
        # Publish startup event
        await self.publish(Event(
            event_type=EventType.SYSTEM_STARTUP,
            action="event_bus_started",
            metadata={"component": "event_bus"}
        ))
    
    async def stop(self):
        """Stop the event bus worker."""
        if not self._running:
            return
        
        # Publish shutdown event
        await self.publish(Event(
            event_type=EventType.SYSTEM_SHUTDOWN,
            action="event_bus_stopping",
            metadata={"component": "event_bus", "stats": self._stats}
        ))
        
        self._running = False
        
        if self._worker_task:
            # Wait for remaining events to be processed
            await asyncio.sleep(0.1)  # Give it time to process remaining events
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Event bus stopped", stats=self._stats)
    
    def subscribe(self, event_type: EventType, handler: EventHandler):
        """Subscribe to events of a specific type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        self._handlers[event_type].append(handler)
        logger.debug("Handler subscribed", event_type=event_type.value)
    
    def unsubscribe(self, event_type: EventType, handler: EventHandler):
        """Unsubscribe from events of a specific type."""
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                logger.debug("Handler unsubscribed", event_type=event_type.value)
            except ValueError:
                pass
    
    async def publish(self, event: Event):
        """Publish an event to the bus."""
        if not self._running:
            logger.warning("Event bus not running, dropping event", event_type=event.event_type.value)
            return
        
        try:
            await self._event_queue.put(event)
            self._stats["events_published"] += 1
            logger.debug("Event published", event_type=event.event_type.value, event_id=event.event_id)
        except Exception as e:
            logger.error("Failed to publish event", error=str(e), event_type=event.event_type.value)
    
    async def _process_events(self):
        """Process events from the queue."""
        while self._running:
            try:
                # Wait for events with timeout to allow graceful shutdown
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._handle_event(event)
                self._stats["events_processed"] += 1
                
            except asyncio.TimeoutError:
                continue  # No events to process, check if still running
            except Exception as e:
                logger.error("Error processing events", error=str(e))
                self._stats["events_failed"] += 1
    
    async def _handle_event(self, event: Event):
        """Handle a single event by calling all registered handlers."""
        handlers = self._handlers.get(event.event_type, [])
        
        if not handlers:
            logger.debug("No handlers for event", event_type=event.event_type.value)
            return
        
        # Call all handlers concurrently
        handler_tasks = []
        for handler in handlers:
            task = asyncio.create_task(self._safe_call_handler(handler, event))
            handler_tasks.append(task)
        
        if handler_tasks:
            await asyncio.gather(*handler_tasks, return_exceptions=True)
    
    async def _safe_call_handler(self, handler: EventHandler, event: Event):
        """Safely call an event handler with error handling."""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            logger.error(
                "Event handler error",
                error=str(e),
                event_type=event.event_type.value,
                event_id=event.event_id,
                handler=str(handler)
            )
            
            # Publish error event
            error_event = Event(
                event_type=EventType.ERROR_OCCURRED,
                action="handler_error",
                outcome="error",
                data={
                    "original_event_type": event.event_type.value,
                    "original_event_id": event.event_id,
                    "handler": str(handler),
                    "error": str(e)
                }
            )
            
            # Avoid infinite recursion by not processing error events for error handlers
            if event.event_type != EventType.ERROR_OCCURRED:
                await self.publish(error_event)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        return {
            **self._stats,
            "queue_size": self._event_queue.qsize(),
            "handler_count": sum(len(handlers) for handlers in self._handlers.values()),
            "event_types_subscribed": len(self._handlers)
        }

# Global event bus instance
event_bus = EventBus()

# Convenience functions for common event types
async def publish_auth_event(event_type: EventType, user_id: str, outcome: str = "success", **kwargs):
    """Publish authentication-related event."""
    # Extract only valid Event fields from kwargs
    valid_fields = {
        'session_id', 'resource_type', 'resource_id', 'action',
        'data', 'metadata', 'ip_address', 'user_agent'
    }
    
    # Filter kwargs to only include valid Event fields
    filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_fields}
    
    # Put any extra fields in metadata
    extra_fields = {k: v for k, v in kwargs.items() if k not in valid_fields}
    if extra_fields:
        metadata = filtered_kwargs.get('metadata', {})
        metadata.update(extra_fields)
        filtered_kwargs['metadata'] = metadata
    
    event = Event(
        event_type=event_type,
        user_id=user_id,
        action=event_type.value.split('.')[-1],
        outcome=outcome,
        **filtered_kwargs
    )
    await event_bus.publish(event)

async def publish_api_event(event_type: EventType, endpoint: str, method: str, status_code: int = 200, **kwargs):
    """Publish API-related event."""
    event = Event(
        event_type=event_type,
        action=f"{method} {endpoint}",
        outcome="success" if 200 <= status_code < 400 else "failure",
        data={"endpoint": endpoint, "method": method, "status_code": status_code},
        **kwargs
    )
    await event_bus.publish(event)

async def publish_data_event(event_type: EventType, resource_type: str, resource_id: str, **kwargs):
    """Publish data-related event."""
    event = Event(
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        action=event_type.value.split('.')[-1],
        **kwargs
    )
    await event_bus.publish(event)