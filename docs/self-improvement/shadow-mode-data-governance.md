# Shadow-Mode Data Governance

Allowed inputs:

- trace reference IDs
- evaluation reference IDs
- outcome reference IDs
- experience reference IDs
- lesson reference IDs
- pattern reference IDs
- safe fingerprints
- redacted numeric metrics
- bounded timestamps
- synthetic test metadata
- operator-selected scope labels

Disallowed inputs:

- raw prompt
- raw hidden reasoning
- chain of thought
- raw user message
- credential
- token
- cookie
- authorization header
- private key
- provider payload
- raw source patch
- raw diff
- unredacted personal data
- arbitrary filesystem path
- URL
- network location
- executable command

Required controls:

- Evidence files must be synthetic, redacted, and read-only.
- Shadow observations must store summaries and references, not sensitive source
  material.
- Operator review items must expose only bounded fields and must not contain
  secrets.
- Shadow mode must consume references through injected read-only adapters.
- Shadow mode must not query arbitrary sources, discover network endpoints from
  input, or execute commands from input.
- Any finding requiring source change must remain a proposal for a later
  explicit authorization.
