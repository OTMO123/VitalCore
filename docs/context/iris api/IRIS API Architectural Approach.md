Architectural Approaches for IRIS API Client:
1. Monolithic Client Pattern

Single class handling all functionality (auth, circuit breaker, encryption, etc.)
Pros: Simple to understand, fewer moving parts
Cons: Hard to test individual components, violates single responsibility

2. Layered Architecture Pattern ⭐

Separate layers: Transport → Security → Resilience → Business Logic
Pros: Clear separation of concerns, easy to test each layer
Cons: More complex initial setup

3. Middleware Chain Pattern

Request flows through a chain of middleware (auth → encryption → rate limit → etc.)
Pros: Highly modular, easy to add/remove features
Cons: Can be harder to debug, potential performance overhead

4. Strategy Pattern with Plugins

Core client with pluggable strategies for auth, retry, circuit breaker
Pros: Maximum flexibility, easy to swap implementations
Cons: More abstraction layers, potential over-engineering

Given your requirements for:

Healthcare compliance (PHI encryption)
High reliability (circuit breaker, retries)
Observability (metrics, tracing)
Testability (mock mode)

