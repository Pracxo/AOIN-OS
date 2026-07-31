# Model Gateway Session

AION-233 starts one local model-gateway session from a validated AION-232 authorization envelope and a bound AION-231 parent secure-runtime session. The session limit is one active gateway session, one hundred requests per session, four concurrent requests, and one million estimated session tokens.

Session close releases active requests and retained request references. The repository is in-memory only and creates no database, file persistence, scheduler, worker, or background continuation.
