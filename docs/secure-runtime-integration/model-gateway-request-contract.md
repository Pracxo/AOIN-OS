# Model Gateway Request Contract

A model-request envelope is local, bounded, fingerprinted, and redacted. It carries no credential reference, network target, executable target, connector target, tool target, production target, retained prompt body, or retained model response body.

Every request preserves `operator_invoked=true`, `local_session=true`, `simulation_only=true`, and `actual_provider_call=false`.
