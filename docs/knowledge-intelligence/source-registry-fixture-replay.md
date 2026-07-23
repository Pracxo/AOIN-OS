# Source Registry Fixture Replay

AION-207 supports explicit synthetic local fixture replay for operator-supplied validation only.

Fixture requirements:

- Absolute path.
- Existing regular file.
- Outside the canonical repository.
- Not a symlink, directory, device file, hidden path, relative path, environment-expanded path, home-expanded path, or network URI.
- Bounded size.
- UTF-8 JSON.
- Exact fixture schema.
- No extra fields.
- `synthetic=true`, `read_only=true`, `redacted=true`.
- At most 100 registry records.
- No source body, raw URL, protected material, persistent write, or runtime effect.

Replay validates every envelope, sequence number, fingerprint chain, and protected-material boundary, then reconstructs immutable in-memory state. It creates no tracked file and applies no persistent write.
