# Asset Verification

Before the draft prerelease can be published, every uploaded asset is downloaded into a temporary verification directory and compared to the retained local candidate file by SHA-256.

Detached signatures are verified against the retained qualification public key. Verification must fail closed on any missing asset, hash mismatch, signature mismatch, stable tag, or production publication side effect.
