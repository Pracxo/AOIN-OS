
# Temporal Claim-Evidence Graph Time Model

The graph separates valid time from transaction time. Valid-time intervals describe when an unverified claim assertion purports to apply. Transaction time records when AION observed or projected the assertion.

AION-209 must preserve non-overlap, timezone-explicit UTC transaction timestamps, open-ended interval ambiguity, and historical claim context without treating non-overlap as contradiction.
