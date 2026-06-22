# AION Deprecation Policy

AION deprecations are metadata records, not runtime removals. A deprecated
feature remains visible in the feature registry until a later migration or
release task removes it.

## Policy

- Deprecations require a reason.
- Deprecation records must be scoped.
- Feature keys remain generic and domain-neutral.
- Deprecation metadata must not include secret-like keys.
- Modules must not self-authorize around deprecated features.

The default v0.1 deprecation policy is conservative: mark deprecated, document
replacement guidance, keep compatibility, and remove only through a later
versioned migration.
