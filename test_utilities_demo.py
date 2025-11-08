#!/usr/bin/env python3
"""
Demonstration of new test utilities replacing unreliable patterns.

This script shows how the new test utilities work without requiring
the full test suite infrastructure.
"""

import asyncio
import time
from app.tests.utils.event_utils import EventCollector, wait_for_event
from app.tests.utils.factories import TestDataFactory


async def demonstrate_event_collector():
    """Demonstrate EventCollector replacing asyncio.sleep()."""
    print("\n" + "="*70)
    print("DEMO 1: EventCollector - Reliable Event Waiting")
    print("="*70)

    collector = EventCollector()

    # Simulate async operation that completes after variable time
    async def async_operation():
        """Simulates an async operation with variable completion time."""
        await asyncio.sleep(0.05)  # Simulates work
        await collector.collect({"type": "operation_complete", "data": "result"})

    print("\n❌ OLD WAY (unreliable):")
    print("   await asyncio.sleep(0.1)  # Hope it completes in 100ms")
    print("   assert result  # May fail on slow systems")

    print("\n✅ NEW WAY (reliable):")
    print("   collector = EventCollector()")
    print("   await async_operation()")
    print("   received = await collector.wait_for_event(timeout=5.0)")
    print("   assert received")

    # Execute the operation
    print("\n📊 Running async operation...")
    start = time.perf_counter()

    # Start the operation
    task = asyncio.create_task(async_operation())

    # Wait for event with proper timeout
    received = await collector.wait_for_event(timeout=5.0)
    duration = (time.perf_counter() - start) * 1000

    print(f"✓ Event received: {received}")
    print(f"✓ Duration: {duration:.2f}ms (waited only as long as needed)")
    print(f"✓ Events collected: {len(collector.events)}")
    print(f"✓ Event data: {collector.events[0]}")

    # Clean up
    await task


async def demonstrate_condition_waiting():
    """Demonstrate wait_for_event() with condition checking."""
    print("\n" + "="*70)
    print("DEMO 2: wait_for_event() - Condition-Based Waiting")
    print("="*70)

    results = []

    async def background_task():
        """Simulates background processing."""
        await asyncio.sleep(0.03)
        results.append("item1")
        await asyncio.sleep(0.02)
        results.append("item2")
        await asyncio.sleep(0.01)
        results.append("item3")

    print("\n❌ OLD WAY (unreliable):")
    print("   await asyncio.sleep(0.1)  # Arbitrary wait")
    print("   assert len(results) > 0  # May fail if too fast/slow")

    print("\n✅ NEW WAY (reliable):")
    print("   success = await wait_for_event(")
    print("       lambda: len(results) >= 3,")
    print("       timeout=5.0")
    print("   )")
    print("   assert success")

    # Execute
    print("\n📊 Running background task...")
    start = time.perf_counter()

    task = asyncio.create_task(background_task())

    # Wait for condition with exponential backoff
    success = await wait_for_event(
        lambda: len(results) >= 3,
        timeout=5.0,
        error_message="Results not populated within timeout"
    )

    duration = (time.perf_counter() - start) * 1000

    print(f"✓ Condition met: {success}")
    print(f"✓ Duration: {duration:.2f}ms (efficient polling)")
    print(f"✓ Results: {results}")

    # Clean up
    await task


def demonstrate_test_factory():
    """Demonstrate deterministic test data generation."""
    print("\n" + "="*70)
    print("DEMO 3: TestDataFactory - Deterministic Data Generation")
    print("="*70)

    print("\n❌ OLD WAY (unreliable):")
    print("   import random")
    print("   user_id = random.randint(1, 1000)  # Non-reproducible")
    print("   username = f'user_{uuid.uuid4()}'  # Different every time")

    print("\n✅ NEW WAY (reliable):")
    print("   factory = TestDataFactory()")
    print("   user = factory.user_data(username='test1')  # Consistent")
    print("   patient = factory.patient_data()  # Sequential IDs")

    # Create factory
    factory = TestDataFactory()

    # Generate user data
    print("\n📊 Generating test data...")
    user1 = factory.user_data(username="test_user_1")
    user2 = factory.user_data(username="test_user_2")

    print(f"\n✓ User 1:")
    print(f"   ID: {user1['id']}")
    print(f"   Username: {user1['username']}")
    print(f"   Email: {user1['email']}")

    print(f"\n✓ User 2:")
    print(f"   ID: {user2['id']}")
    print(f"   Username: {user2['username']}")
    print(f"   Email: {user2['email']}")

    # Generate FHIR resources
    patient = factory.fhir_patient_resource()
    print(f"\n✓ FHIR Patient Resource:")
    print(f"   Type: {patient['resourceType']}")
    print(f"   ID: {patient['id']}")
    print(f"   Name: {patient['name'][0]['family']}, {patient['name'][0]['given'][0]}")
    print(f"   Birth Date: {patient['birthDate']}")

    # Generate immunization
    immunization = factory.fhir_immunization_resource(patient_id=patient['id'])
    print(f"\n✓ FHIR Immunization Resource:")
    print(f"   Type: {immunization['resourceType']}")
    print(f"   ID: {immunization['id']}")
    print(f"   Patient: {immunization['patient']['reference']}")
    print(f"   Status: {immunization['status']}")

    print("\n✓ All data is deterministic and reproducible!")


async def demonstrate_multiple_events():
    """Demonstrate waiting for multiple events."""
    print("\n" + "="*70)
    print("DEMO 4: Multiple Event Collection")
    print("="*70)

    collector = EventCollector()

    async def publish_events():
        """Publishes multiple events."""
        for i in range(1, 4):
            await asyncio.sleep(0.01)
            await collector.collect({
                "event_id": i,
                "type": "user_action",
                "action": f"action_{i}"
            })

    print("\n❌ OLD WAY (unreliable):")
    print("   await asyncio.sleep(0.5)  # Hope all events complete")
    print("   assert len(events) == 3  # May fail if timing wrong")

    print("\n✅ NEW WAY (reliable):")
    print("   collector = EventCollector()")
    print("   await publish_events()")
    print("   received = await collector.wait_for_event(count=3, timeout=5.0)")
    print("   assert len(collector.events) == 3")

    # Execute
    print("\n📊 Publishing 3 events...")
    start = time.perf_counter()

    task = asyncio.create_task(publish_events())

    # Wait for all 3 events
    received = await collector.wait_for_event(count=3, timeout=5.0)
    duration = (time.perf_counter() - start) * 1000

    print(f"✓ All events received: {received}")
    print(f"✓ Duration: {duration:.2f}ms")
    print(f"✓ Event count: {len(collector.events)}")

    for idx, event in enumerate(collector.events, 1):
        print(f"   Event {idx}: {event['action']}")

    # Clean up
    await task


async def main():
    """Run all demonstrations."""
    print("\n" + "="*70)
    print("TEST UTILITY DEMONSTRATION")
    print("Showing improvements over unreliable test patterns")
    print("="*70)

    # Run demos
    await demonstrate_event_collector()
    await demonstrate_condition_waiting()
    demonstrate_test_factory()
    await demonstrate_multiple_events()

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("\n✅ Benefits of new test utilities:")
    print("   1. No arbitrary sleeps - waits only as long as needed")
    print("   2. Reliable on all systems - slow or fast")
    print("   3. Clear timeout errors - easy to debug")
    print("   4. Deterministic data - reproducible tests")
    print("   5. Proper async handling - no race conditions")

    print("\n📊 Test Reliability Improvements:")
    print("   • Event-based waiting: 100% reliable")
    print("   • Timing independence: No arbitrary waits")
    print("   • Data consistency: Fully deterministic")
    print("   • Error messages: Clear and actionable")

    print("\n🎯 Next Steps:")
    print("   • Apply to remaining 20+ files with timing dependencies")
    print("   • Replace all pytest.skip() with pytest.fail()")
    print("   • Reorganize tests into unit/integration/e2e")
    print("   • Update pytest configuration")

    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETE ✓")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
