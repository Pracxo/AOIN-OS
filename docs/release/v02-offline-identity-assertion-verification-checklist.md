# v0.2 Offline Identity Assertion Verification Checklist

- [x] AION-161 authorization verified.
- [x] Exact dependency `cryptography>=49.0.0,<50.0.0` added.
- [x] Strict assertion payload and envelope contracts added.
- [x] Fixed Ed25519 verification added.
- [x] Domain-separated canonical payloads added.
- [x] Strict unpadded base64url helpers added.
- [x] Immutable public-key registry added.
- [x] Rotation, revocation, inactive, retired, and unknown key states tested.
- [x] Temporal and claim constraints tested.
- [x] Replay boundary remains unimplemented and documented.
- [x] Request authentication remains disabled.
- [x] Runtime integration remains absent.
- [x] v0.2 tag and release remain absent.
- [ ] Formal AION-161 lifecycle closeout by AION-163.


## AION-163 Replay Protection Authorization Update

AION-163 records AION-162 PR #72 and corrective PR #73 as the completed offline verification delivery, closes `AION-161-PA-0006` as inactive, consumed, expired, and non-reusable, and creates `AION-163-PA-0007` as the sole active authorization for AION-164 persistent identity-assertion replay protection. The next critical path is AION-164. Runtime request authentication, ActorContext application, RequestIdentityContext application, dependency changes, migrations, production schema auto-create, package files, lockfiles, v0.2 tags, and v0.2 releases remain blocked.
