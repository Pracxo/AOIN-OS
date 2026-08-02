# AION-243 Source Snapshot

The candidate source snapshot is created from the clean candidate source commit,
not from the mutable working directory.

The runner builds two deterministic source archives with fixed metadata and
requires matching SHA-256 values. The retained archive is stored in the local
candidate bundle as `source/aion-v0.2.0-rc.1-source.tar.gz`.

The source snapshot rejects unsafe paths, parent traversal and symbolic or hard
links escaping the archive.
