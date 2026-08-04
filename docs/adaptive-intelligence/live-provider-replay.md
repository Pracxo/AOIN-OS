# AION-248 Replay

Exact replay returns the prior safe request projection without performing a second provider call. Changed replay under an existing request ID is rejected before credential access or transport.

Replay state is in memory only and is cleared after evidence projection. No replay store, database table, file or background worker is introduced.
