# Model Gateway Circuit Breaker Implementation

The circuit breaker is local, deterministic, in-memory, and explicit-transition-only. It supports `closed`, `open`, and `half_open` states.

Open state blocks routing. Half-open state permits deterministic reference simulation only. There is no provider network failure ingestion, background reset, timer thread, daemon, or automatic half-open transition.
