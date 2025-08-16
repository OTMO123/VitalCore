"""
Tests for the Hybrid Event Bus

Comprehensive test suite covering:
- Event publishing and subscription
- Circuit breaker functionality
- Dead letter queue handling
- Integrity verification
- Performance under load
- Graceful shutdown
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from typing import List

from app.core.event_bus_advanced import (
    HybridEventBus, BaseEvent, EventHandler, TypedEventHandler,
    AggregateQueue, CircuitBreakerState, DeadLetterQueue,
    EventMetadata, EventPriority, DeliveryMode
)

# Test Events
class EventBusEventBusTestEvent(BaseEvent):
    """Test event for unit tests."""
    test_data: str = "test"

class AnotherEventBusTestEvent(BaseEvent):
    """Another test event."""
    value: int = 42

# Test Handlers
class EventBusTestHandler(EventHandler):
    """Test event handler."""
    
    def __init__(self, handler_name: str, should_fail: bool = False):
        super().__init__(handler_name)
        self.should_fail = should_fail
        self.events_received = []
    
    async def handle(self, event: BaseEvent) -> bool:
        self.events_received.append(event)
        if self.should_fail:
            raise Exception("Handler intentionally failed")
        return True

class SlowEventHandler(EventHandler):
    """Slow event handler for timeout testing."""
    
    def __init__(self, handler_name: str, delay_seconds: float = 2.0):
        super().__init__(handler_name)
        self.delay_seconds = delay_seconds
        self.events_received = []
    
    async def handle(self, event: BaseEvent) -> bool:
        await asyncio.sleep(self.delay_seconds)
        self.events_received.append(event)
        return True

class TypedTestHandler(TypedEventHandler):
    """Typed test handler."""
    
    def __init__(self, handler_name: str):
        super().__init__(handler_name, [EventBusEventBusTestEvent])
        self.events_received = []
    
    async def handle(self, event: BaseEvent) -> bool:
        self.events_received.append(event)
        return True

@pytest.fixture
def mock_db_session_factory():
    """Mock database session factory."""
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    
    def factory():
        return mock_session
    
    return factory

@pytest.fixture
async def event_bus(mock_db_session_factory):
    """Create event bus for testing."""
    bus = HybridEventBus(mock_db_session_factory)
    await bus.start()
    yield bus
    await bus.stop()

class EventBusTestEventBusBasics:
    """Test basic event bus functionality."""
    
    @pytest.mark.asyncio
    async def test_event_publishing_and_subscription(self, event_bus):
        """Test basic event publishing and subscription."""
        handler = EventBusEventBusTestHandler("test_handler")
        event_bus.subscribe(handler)
        
        event = EventBusTestEvent(
            aggregate_id="test_aggregate",
            aggregate_type="test",
            publisher="test_publisher"
        )
        
        # Publish event
        success = await event_bus.publish(event)
        assert success
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Verify handler received event
        assert len(handler.events_received) == 1
        assert handler.events_received[0].event_id == event.event_id
    
    @pytest.mark.asyncio
    async def test_typed_event_handler(self, event_bus):
        """Test typed event handler only receives correct types."""
        typed_handler = TypedTestHandler("typed_handler")
        general_handler = EventBusEventBusTestHandler("general_handler")
        
        event_bus.subscribe(typed_handler)
        event_bus.subscribe(general_handler)
        
        test_event = EventBusTestEvent(
            aggregate_id="test_aggregate",
            aggregate_type="test",
            publisher="test_publisher"
        )
        
        another_event = AnotherEventBusTestEvent(
            aggregate_id="test_aggregate",
            aggregate_type="test", 
            publisher="test_publisher"
        )
        
        # Publish both events
        await event_bus.publish(test_event)
        await event_bus.publish(another_event)
        
        await asyncio.sleep(0.1)
        
        # Typed handler should only receive EventBusTestEvent
        assert len(typed_handler.events_received) == 1
        assert isinstance(typed_handler.events_received[0], EventBusTestEvent)
        
        # General handler should receive both
        assert len(general_handler.events_received) == 2
    
    @pytest.mark.asyncio
    async def test_multiple_handlers_same_event(self, event_bus):
        """Test multiple handlers can process the same event."""
        handler1 = EventBusEventBusTestHandler("handler1")
        handler2 = EventBusEventBusTestHandler("handler2")
        
        event_bus.subscribe(handler1)
        event_bus.subscribe(handler2)
        
        event = EventBusTestEvent(
            aggregate_id="test_aggregate",
            aggregate_type="test",
            publisher="test_publisher"
        )
        
        await event_bus.publish(event)
        await asyncio.sleep(0.1)
        
        # Both handlers should receive the event
        assert len(handler1.events_received) == 1
        assert len(handler2.events_received) == 1
        assert handler1.events_received[0].event_id == handler2.events_received[0].event_id

class TestAggregateOrdering:
    """Test per-aggregate event ordering."""
    
    @pytest.mark.asyncio
    async def test_aggregate_queue_ordering(self):
        """Test events are processed in order for same aggregate."""
        queue = AggregateQueue("test_aggregate")
        
        events = []
        for i in range(5):
            event = EventBusTestEvent(
                aggregate_id="test_aggregate",
                aggregate_type="test",
                publisher="test_publisher",
                test_data=f"event_{i}"
            )
            events.append(event)
            await queue.enqueue(event)
        
        # Dequeue all events
        received_events = []
        while not queue.is_empty():
            event = await queue.dequeue()
            if event:
                received_events.append(event)
        
        # Verify order
        assert len(received_events) == 5
        for i, event in enumerate(received_events):
            assert event.test_data == f"event_{i}"
    
    @pytest.mark.asyncio
    async def test_different_aggregates_parallel_processing(self, event_bus):
        """Test events from different aggregates can be processed in parallel."""
        handler = EventBusEventBusTestHandler("test_handler")
        event_bus.subscribe(handler)
        
        # Create events for different aggregates
        events = []
        for i in range(10):
            event = EventBusTestEvent(
                aggregate_id=f"aggregate_{i % 2}",  # Two different aggregates
                aggregate_type="test",
                publisher="test_publisher",
                test_data=f"event_{i}"
            )
            events.append(event)
            await event_bus.publish(event)
        
        await asyncio.sleep(0.2)
        
        # All events should be processed
        assert len(handler.events_received) == 10

class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self, event_bus):
        """Test circuit breaker opens after threshold failures."""
        failing_handler = EventBusEventBusTestHandler("failing_handler", should_fail=True)
        failing_handler.circuit_breaker.failure_threshold = 3
        
        event_bus.subscribe(failing_handler)
        
        # Send events that will fail
        for i in range(5):
            event = EventBusTestEvent(
                aggregate_id="test_aggregate",
                aggregate_type="test",
                publisher="test_publisher"
            )
            await event_bus.publish(event)
        
        await asyncio.sleep(0.2)
        
        # Circuit breaker should be open
        assert failing_handler.circuit_breaker.state == "open"
        assert failing_handler.circuit_breaker.failure_count >= 3
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_prevents_calls_when_open(self, event_bus):
        """Test circuit breaker prevents calls when open."""
        handler = EventBusEventBusTestHandler("test_handler")
        handler.circuit_breaker.state = "open"
        handler.circuit_breaker.last_failure_time = datetime.utcnow()
        
        event_bus.subscribe(handler)
        
        event = EventBusTestEvent(
            aggregate_id="test_aggregate",
            aggregate_type="test",
            publisher="test_publisher"
        )
        
        await event_bus.publish(event)
        await asyncio.sleep(0.1)
        
        # Handler should not receive event due to open circuit breaker
        assert len(handler.events_received) == 0

class TestBackpressure:
    """Test backpressure handling."""
    
    @pytest.mark.asyncio
    async def test_queue_backpressure(self):
        """Test queue applies backpressure when full."""
        queue = AggregateQueue("test_aggregate", max_size=3)
        
        # Fill the queue
        for i in range(3):
            event = EventBusTestEvent(
                aggregate_id="test_aggregate",
                aggregate_type="test",
                publisher="test_publisher"
            )
            success = await queue.enqueue(event)
            assert success
        
        # Next event should fail due to backpressure
        overflow_event = EventBusTestEvent(
            aggregate_id="test_aggregate",
            aggregate_type="test",
            publisher="test_publisher"
        )
        
        success = await queue.enqueue(overflow_event)
        assert not success  # Should fail due to full queue

class TestDeadLetterQueue:
    """Test dead letter queue functionality."""
    
    @pytest.mark.asyncio
    async def test_dead_letter_queue_storage(self):
        """Test failed events are stored in dead letter queue."""
        dlq = DeadLetterQueue(max_size=100)
        
        event = EventBusTestEvent(
            aggregate_id="test_aggregate",
            aggregate_type="test",
            publisher="test_publisher"
        )
        
        await dlq.add_event(event, "Handler failed", "test_handler")
        
        assert dlq.metrics["events_added"] == 1
        assert dlq.metrics["current_size"] == 1
        assert len(dlq.events) == 1
    
    @pytest.mark.asyncio
    async def test_dead_letter_queue_replay(self, event_bus):
        """Test replaying events from dead letter queue."""
        dlq = event_bus.dead_letter_queue
        handler = EventBusEventBusTestHandler("test_handler")
        event_bus.subscribe(handler)
        
        # Add event to DLQ
        event = EventBusTestEvent(
            aggregate_id="test_aggregate",
            aggregate_type="test",
            publisher="test_publisher"
        )
        
        await dlq.add_event(event, "Test failure", "test_handler")
        
        # Replay events
        replayed = await dlq.replay_events(event_bus, max_events=10)
        
        assert replayed == 1
        await asyncio.sleep(0.1)
        
        # Handler should receive replayed event
        assert len(handler.events_received) == 1

class EventBusTestEventIntegrity:
    """Test event integrity and metadata."""
    
    def test_event_checksum_calculation(self):
        """Test event checksum calculation for integrity."""
        event = EventBusTestEvent(
            aggregate_id="test_aggregate",
            aggregate_type="test",
            publisher="test_publisher",
            test_data="test_data"
        )
        
        checksum1 = event.calculate_checksum()
        checksum2 = event.calculate_checksum()
        
        # Same event should produce same checksum
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA-256 hex length
    
    def test_event_metadata_extraction(self):
        """Test event metadata extraction."""
        event = EventBusTestEvent(
            aggregate_id="test_aggregate",
            aggregate_type="test",
            publisher="test_publisher",
            priority=EventPriority.HIGH,
            delivery_mode=DeliveryMode.AT_LEAST_ONCE
        )
        
        metadata = event.get_metadata()
        
        assert metadata.aggregate_id == "test_aggregate"
        assert metadata.aggregate_type == "test"
        assert metadata.publisher == "test_publisher"
        assert metadata.priority == EventPriority.HIGH
        assert metadata.delivery_mode == DeliveryMode.AT_LEAST_ONCE

class TestPerformance:
    """Test event bus performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_high_throughput_publishing(self, event_bus):
        """Test publishing many events quickly."""
        handler = EventBusEventBusTestHandler("test_handler")
        event_bus.subscribe(handler)
        
        # Publish 1000 events
        events_to_publish = 1000
        
        start_time = datetime.utcnow()
        
        for i in range(events_to_publish):
            event = EventBusTestEvent(
                aggregate_id=f"aggregate_{i % 10}",  # 10 different aggregates
                aggregate_type="test",
                publisher="test_publisher",
                test_data=f"event_{i}"
            )
            await event_bus.publish(event)
        
        # Wait for processing
        await asyncio.sleep(2.0)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Verify throughput
        events_per_second = events_to_publish / duration
        
        print(f"Published {events_to_publish} events in {duration:.2f}s")
        print(f"Throughput: {events_per_second:.2f} events/second")
        print(f"Events processed: {len(handler.events_received)}")
        
        # Should process most events (allowing for some in-flight)
        assert len(handler.events_received) >= events_to_publish * 0.9
    
    @pytest.mark.asyncio
    async def test_memory_usage_with_many_events(self, event_bus):
        """Test memory usage doesn't grow unbounded."""
        handler = EventBusEventBusTestHandler("test_handler")
        event_bus.subscribe(handler)
        
        # Publish many events to different aggregates
        for i in range(100):
            event = EventBusTestEvent(
                aggregate_id=f"aggregate_{i}",
                aggregate_type="test",
                publisher="test_publisher"
            )
            await event_bus.publish(event)
        
        await asyncio.sleep(0.5)
        
        # Check that empty queues are cleaned up
        initial_queue_count = len(event_bus.aggregate_queues)
        
        # Wait for processing and cleanup
        await asyncio.sleep(1.0)
        
        final_queue_count = len(event_bus.aggregate_queues)
        
        # Empty queues should be cleaned up
        assert final_queue_count <= initial_queue_count

class TestGracefulShutdown:
    """Test graceful shutdown with in-flight events."""
    
    @pytest.mark.asyncio
    async def test_graceful_shutdown_waits_for_events(self, mock_db_session_factory):
        """Test shutdown waits for in-flight events to complete."""
        bus = HybridEventBus(mock_db_session_factory)
        await bus.start()
        
        slow_handler = SlowEventHandler("slow_handler", delay_seconds=0.5)
        bus.subscribe(slow_handler)
        
        # Publish event that takes time to process
        event = EventBusTestEvent(
            aggregate_id="test_aggregate",
            aggregate_type="test",
            publisher="test_publisher"
        )
        
        await bus.publish(event)
        
        # Start shutdown immediately
        start_time = datetime.utcnow()
        await bus.stop(timeout=2.0)
        end_time = datetime.utcnow()
        
        # Should have waited for event processing
        duration = (end_time - start_time).total_seconds()
        assert duration >= 0.4  # Almost the full delay time
        
        # Event should have been processed
        assert len(slow_handler.events_received) == 1

class TestMetrics:
    """Test event bus metrics collection."""
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, event_bus):
        """Test metrics are collected correctly."""
        handler = EventBusEventBusTestHandler("test_handler")
        event_bus.subscribe(handler)
        
        # Publish some events
        for i in range(5):
            event = EventBusTestEvent(
                aggregate_id="test_aggregate",
                aggregate_type="test",
                publisher="test_publisher"
            )
            await event_bus.publish(event)
        
        await asyncio.sleep(0.2)
        
        # Get metrics
        metrics = event_bus.get_metrics()
        
        # Verify metrics structure
        assert "counters" in metrics
        assert "handlers" in metrics
        assert "aggregate_queues" in metrics
        assert "in_flight_events" in metrics
        assert "running" in metrics
        
        # Verify some basic counts
        assert metrics["running"] == True
        assert len(metrics["handlers"]) == 1
        assert "test_handler" in metrics["handlers"]

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])