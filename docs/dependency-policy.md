# Dependency Policy

- Prefer the Python standard library and small dependencies.
- Keep all external systems behind adapters.
- Do not add provider SDKs in core except inside isolated adapter paths.
- Put optional dependencies in optional dependency groups.
- Do not add domain SDKs in Brain core.
- Do not add a raw secret management dependency until raw secret storage is
  explicitly designed.
- Do not add an untrusted code execution dependency in v0.1.
- Update tests and documentation when dependencies change.
