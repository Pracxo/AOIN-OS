# Connector Release No-Go

The connector release gate fails if any of these no-go conditions are present:

- connector runtime enabled
- external calls enabled
- credentials stored
- tokens stored
- OAuth, OIDC, or SAML runtime enabled
- sandbox execution enabled
- filesystem, network, process, dynamic import, or package install enabled
- policy runtime allow path added
- connector activation enabled
- connector route registration enabled
- provider SDK dependency added
- migration added
- package files added
- API runtime execution route added
- implementation approval changed to true

These checks apply to changed files, untracked files, connector examples,
operator static console demo data, and release-gate scripts. Docs and examples
may describe future implementation only when they keep disabled, denied,
preview-only, no-go, or future-only wording.
