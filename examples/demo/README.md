# AION v0.1 Demo Examples

This folder contains synthetic local-only demo inputs for AION Brain v0.1.

Use them with:

```bash
./scripts/demo-local.sh --offline-ok
examples/demo/local-demo-sequence.sh
```

The extension manifest assumes `local_manifest` source handling through the
extension intake request. It is metadata-only, declares no external
dependencies, does not load code, does not activate bindings, does not register
routes, and does not request external sources or full autonomy.
