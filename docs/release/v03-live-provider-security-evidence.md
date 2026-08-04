# v0.3 Live-Provider Security Evidence

Security evidence is based on exact provider/model/endpoint binding, environment-only credential handling, TLS verification, redirect rejection, proxy bypass, no tools, no files, no previous response state and no raw-content retention.

The local runner is separated from installed runtime source so CI and unit tests cannot accidentally perform provider calls.
