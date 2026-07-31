# Model Gateway System Instruction Policy

AION-233 uses a closed system-instruction policy registry with `aion-safe-text-simulation-v1` and `aion-safe-structured-simulation-v1`. Policy bodies are retained only by fingerprint.

The system policy precedes user messages. User messages cannot replace or override it. Unknown policy codes, override markers, executable instructions, tool instructions, and function instructions fail closed.
