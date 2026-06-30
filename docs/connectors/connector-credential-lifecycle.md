# Connector Credential Lifecycle

AION-113 records the future connector credential lifecycle without creating a credential store.

Lifecycle states:

- `requested`
- `approved_for_future_storage`
- `provisioned_future`
- `rotated_future`
- `revoked_future`
- `expired_future`
- `quarantined_future`
- `deleted_future`

Only `requested` is available as design review metadata today. Every actual storage state is `future_only=true` and `allowed_today=false`. All future storage states require production auth, a secret-store decision, audit, and provenance. Rotation and revocation planning are mandatory before any future material can be provisioned.
